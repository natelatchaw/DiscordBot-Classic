import asyncio
import logging
from asyncio import Event, Queue, Task, TimeoutError
from asyncio.events import AbstractEventLoop
from logging import Logger
from pathlib import Path
from shlex import join
from typing import Any, Dict, List, NoReturn, Optional, Union
from urllib.request import Request

import discord
import youtube_dl
from context import Context
from database import Database
from discord import (Activity, ClientException, Guild, StageChannel, Streaming,
                     TextChannel, User, VoiceChannel, VoiceClient, VoiceState)
from discord.player import AudioSource
from router.configuration import Section
from settings.settings import Settings

from components.models.audio import AudioRequest, Metadata

log: Logger = logging.getLogger(__name__)


class Audio():
    """
    Component responsible for audio playback.
    """

    @property
    def timeout(self) -> float:
        key: str = "timeout"
        value: Optional[str] = None
        try:
            value = self._config[key]
            if value and isinstance(value, str):
                return float(value)
        except KeyError:
            self._config[key] = ""
            return None
        except ValueError:
            self._config[key] = ""
            return None

    @timeout.setter
    def timeout(self, value: float) -> None:
        key: str = "timeout"
        if value: self._config[key] = str(value)        


    def __init__(self, *args, **kwargs):
        self._loop: Optional[AbstractEventLoop] = None
        self._connection: Event = Event()
        self._playback_event: Event = Event()
        self._playback_queue: Queue = Queue()
        self._vclient: Optional[VoiceClient] = None
        self._current: Optional[Metadata] = None

        try:
            self._client: discord.Client = kwargs['client']
            self._settings: Settings = kwargs['settings']
        except KeyError as error:
            raise AudioError(f'Key {error} was not found in provided kwargs', error)

        self.__setup__()

        task: Task[NoReturn] = asyncio.create_task(self.__start__())


    def __setup__(self) -> None:
        # create database instance
        self._database: Database = Database(Path('./archive/audio.db'))
        # create a config section for Audio
        self._settings['Audio'] = Section('Audio', self._settings._parser, self._settings._reference)
        # create reference to Audio config section
        self._config: Section = self._settings['Audio']

    def __on_complete__(self, error: Optional[Exception]):
        """
        Called when a source completes in the audio loop.
        This is used internally and should not be called as a command.
        """
        # set the playback event
        self._playback_event.set()
        # log error if available
        if error: log.error(error)

    async def __on_dequeue__(self, metadata: Metadata) -> None:
        """
        Called when a source is retrieved from the top of the queue.
        This is used internally and should not be called as a command.
        """
        # set the current metadata
        self._current: Optional[Metadata] = metadata
        # instantiate activity
        activity: Activity = Streaming(name=metadata.title)
        # change the client's presence
        await self._client.change_presence(activity=activity)

    async def __start__(self):
        """
        The core audio playback loop.
        This is used internally and should not be called as a command.
        """

        while True:
            try:
                log.debug(f'Beginning core audio playback loop.')

                # wait for the connection event to be set
                _: True = await self._connection.wait()

                # if the VoiceClient is not available
                if self._vclient is None:
                    log.debug(f'No voice client available.')
                    log.debug('Resetting...')
                    # clear the connection event
                    self._connection.clear()
                    # restart the loop
                    continue

                log.debug(f'Waiting for next audio request')

                # get an audio request from the queue
                request: AudioRequest = await asyncio.wait_for(self._playback_queue.get(), self.timeout)

                # update presence
                await self.__on_dequeue__(request.metadata)

                log.debug(f'Beginning track \'{request.metadata.title}\'')

                # clear the playback event
                self._playback_event.clear()

                # play the request
                self._vclient.play(request.source, after=self.__on_complete__)

                # wait for the playback event to be set
                _: True = await self._playback_event.wait()

                log.debug(f'Finishing track \'{request.metadata.title}\'')

            except TimeoutError as error:
                log.error(error)
                if self._vclient:
                    await self._vclient.disconnect(force=True)
                    self._vclient: Optional[VoiceClient] = None
                self._connection.clear()

            except Exception as error:
                log.error(error)
                self._connection.clear()
    
    
    async def __queue__(self, context: Context, *, url: str = None, search: str = None, speed: str = None) -> Request:
        """
        Add source media to the media queue.

        Parameters:
            - url: A URL link to a YouTube video to add to the queue.
            - search: Search terms to query YouTube for a source video.
        """

        if not url and not search:
            raise ValueError("Invalid or missing URL/search query provided.")

        try:
            youtube_dl_options: Dict[str, Any] = {
                'format': 'bestaudio/best',
                'noplaylist': False,
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'opus',
                    },
                ],
                'logger': AudioLogger(),
                'progress_hooks': [ ],
            }

            try: 
                query: str = url if url else f'ytsearch:{search}'
                data: Dict[str, Any] = youtube_dl.YoutubeDL(youtube_dl_options).extract_info(query, download=False)
                # get the entries property, if it exists
                entries: Optional[List[Any]] = data.get('entries')
                # if the data contains a list of entries, use the list
                # otherwise create list from data (single entry)
                results: List[Dict[str, Any]] = entries if entries else [data]
            except youtube_dl.utils.DownloadError as downloadError:
                raise downloadError

            result: Optional[Dict[str, Any]] = results[0]
            if not result:
                raise AudioError(f'No results found for `{query}`')
            
            # get multiplier if speed was provided
            multiplier: Optional[float] = float(speed) if speed else None
            # assert the multiplier is within supported bounds
            multiplier: Optional[float] = multiplier if multiplier and multiplier > 0.5 and multiplier < 2.0 else None
            # create options string if multiplier is available
            options: Optional[str] = join([r'-filter:a', rf'atempo={multiplier}']) if multiplier else None

            # create track instance from result data
            metadata: Metadata = Metadata.__from_dict__(result, context.message.id, context.message.author.id)
            # create the metadata table if needed
            self._database.create(metadata)
            # insert the metadata into the table
            self._database.insert(metadata)

            # create source from metadata url and options
            source: AudioSource = discord.FFmpegOpusAudio(metadata.url, options=options)
            # create request from source and metadata
            request: AudioRequest = AudioRequest(source, metadata)
            # add the request to the queue
            await self._playback_queue.put(request)
            # return the request
            return request
        except:
            raise


    async def set_timeout(self, context: Context, *, length: Optional[str] = None):
        """
        Sets the number of seconds the bot should wait before disconnecting
        while idle in a voice channel.

        Parameters:
        - length: the number of seconds to wait
        """
        try:
            self.timeout = float(length) if length else None
            if length is None:
                await context.message.reply(f'Timeout disabled. Bot will not leave the voice channel after the queue is emptied.')
            else:
                await context.message.reply(f'Timeout set to {self.timeout} seconds. Bot will wait for this duration after the queue is empty before leaving the voice channel.')
        except ValueError:
            raise


    async def connect(self, context: Context):
        """
        Joins the user's voice channel.
        """

        state: Optional[VoiceState] = context.message.author.voice
        if not state:
            raise InvalidChannelError(None)

        channel: Optional[Union[VoiceChannel, StageChannel]] = state.channel
        if not channel:
            raise InvalidChannelError(None)

        self._channel: Optional[Union[VoiceChannel, StageChannel]] = state.channel
        try:
            self._vclient: Optional[VoiceClient] = await self._channel.connect()
            self._connection.set()
        except RuntimeError as error:
            raise
        except ClientException as error:
            raise


    async def disconnect(self, context: Context):
        """
        Disconnects the bot from the joined voice channel.
        """

        try:
            if not self._vclient:
                raise ConnectionError('Cannot disconnect: Not connected to begin with.')
            elif not self._vclient.is_connected():
                raise ConnectionError('Cannot disconnect: Not connected to begin with.')
            else:
                self._playback_event.set()
                await self._vclient.disconnect()
        except ConnectionError:
            raise
        except:
            await self._vclient.disconnect(force=True)
        finally:
            self._connection.clear()


    async def play(self, context: Context, *, url: str = None, search: str = None, speed: str = None):
        """
        Plays audio in a voice channel.
        Supports YouTube URLs via the url parameter
        Supports YouTube search via the search parameter

        Parameters:
            - url: A URL link to a YouTube video to add to the queue.
            - search: Search terms to query YouTube for a source video.
            - speed: A playback speed modifier between 0.5 and 2.0
        """

        try:
            # connect to the channel
            await self.connect(context)
        except discord.ClientException:
            # TODO:
            # VoiceClient.connect() - You are already connected to a voice channel.
            # VoiceClient.play() - Already playing audio or not connected.
            pass

        try:
            # queue the requested content
            request: Request = await self.__queue__(context, url=url, search=search, speed=speed)

            embed: discord.Embed = discord.Embed()
            embed.set_author(name=context.message.author.display_name, icon_url=context.message.author.avatar_url)
            embed.title = request.metadata.title
            embed.description = request.metadata.channel
            embed.set_image(url=request.metadata.thumbnail)
            embed.timestamp = context.message.created_at
            embed.color = discord.Colour.from_rgb(r=255, g=0, b=0)
            await context.message.channel.send(embed=embed)

        except discord.ClientException:
            # TODO:
            # VoiceClient.connect() - You are already connected to a voice channel.
            # VoiceClient.play() - Already playing audio or not connected.
            pass
        except TypeError:
            # TODO:
            # VoiceClient.play() - Source is not an AudioSource or after is not a callable.
            raise
        except asyncio.TimeoutError:
            # TODO:
            # VoiceClient.connect() - Could not connect to the voice channel in time.
            raise
        except discord.opus.OpusNotLoaded:
            # TODO:
            # VoiceClient.connect() - The opus library has not been loaded.
            # VoiceClient.play() - Source is not opus encoded and opus is not loaded.
            raise
        finally:
            pass


    async def pause(self, context: Context):
        """
        Pauses audio playback.
        """
        if self._vclient:
            self._vclient.pause()
            return


    async def skip(self, context: Context):
        """
        Skips the current track.
        """
        if self._vclient:
            self._vclient.source = AudioSource()
            return

    
    async def stop(self, context: Context):
        """
        Stops audio playback.
        """
        if self._vclient:
            self._vclient.stop()
            self.disconnect(context)
            return


    async def nightcore(self, context: Context, *, url: str = None, search: str = None, channel: str = None, speed: str = '1.25'):
        """
        Plays audio in a voice channel.
        Supports YouTube URLs via the url parameter,
        and searching YouTube via the search parameter.
        By default, the speed parameter is set to 1.25

        Parameters:
            - url: A URL link to a YouTube video to add to the queue.
            - search: Search terms to query YouTube for a source video.
            - speed: A playback speed modifier between 0.5 and 2.0
        """
        await self.play(context, url=url, search=search, channel=channel, speed=speed)

    async def top(self, context: Context):
        """
        """

        guild: Guild = context.message.guild
        channel: TextChannel = context.message.channel
        user: User = context.message.author

        try:
            mention: Optional[User] = context.message.mentions.pop(0)
            if mention: user = mention
        except IndexError:
            pass

        results: List[Metadata] = [Metadata.__from_row__(result) for result in self._database.select()]


class AudioLogger():
    def debug(self, message: str):
        log.debug(message)

    def warning(self, message: str):
        log.warning(message)
        
    def error(self, message: str):
        log.error(message)


class AudioError(Exception):
    """"""

    def __init__(self, message: str, exception: Optional[Exception] = None):
        self._message = message
        self._inner_exception = exception

    def __str__(self) -> str:
        return self._message


class NotConnectedError(AudioError):
    """"""

    def __init__(self, exception: Optional[Exception] = None):
        message: str = f'The client is not connected to a compatible voice channel.'
        super().__init__(message, exception)


class InvalidChannelError(AudioError):
    """"""

    def __init__(self, channel: Optional[discord.abc.GuildChannel], exception: Optional[Exception] = None):
        reference: str = channel.mention if channel else 'unknown'
        message: str = f'Cannot connect to channel {reference}'
        super().__init__(message, exception)
