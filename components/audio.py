import asyncio
import logging
from asyncio import Event, Queue
from asyncio.events import AbstractEventLoop
from logging import Logger
from typing import Any, Dict, List, Optional, Union

import discord
import youtube_dl
from context import Context
from discord import StageChannel, VoiceChannel, VoiceClient, VoiceState
from discord.player import AudioSource

log: Logger = logging.getLogger(__name__)


class Audio():
    """
    Component description unavailable.
    """

    def __init__(self, *args, **kwargs):
        self._loop: Optional[AbstractEventLoop] = None
        self._connection: Event = Event()
        self._playback_event: Event = Event()
        self._playback_queue: Queue = Queue()
        self._timeout: Optional[float] = None

        asyncio.create_task(self.__start__())


    def __onComplete__(self, error: Optional[Exception]):
        """
        Called when a source completes in the audio loop.
        This is used internally and should not be called as a command.
        """
        # set the playback event
        self._playback_event.set()
        # log error if available
        if error: log.error(error)


    async def __start__(self):
        """
        The core audio playback loop.
        This is used internally and should not be called as a command.
        """

        while True:
            try:
                log.debug(f'Beginning core audio playback loop.')

                # wait for the connection event to be set
                _: True = await asyncio.wait_for(self._connection.wait(), self._timeout)

                # if the VoiceClient is not available
                if self._client is None:
                    log.debug(f'No voice client available.')
                    # clear the playback event
                    self._connection.clear()
                    log.debug('Resetting...')
                    # restart the loop
                    continue

                # if the VoiceClient is not connected
                if not self._client.is_connected():
                    log.debug(f'Voice client is not connected.')
                    # clear the playback event
                    self._connection.clear()
                    log.debug('Resetting...')
                    # restart the loop
                    continue

                log.debug(f'Waiting for next audio request')

                # get an audio request from the queue
                request: AudioRequest = await asyncio.wait_for(self._playback_queue.get(), self._timeout)

                log.debug(f'Beginning track \'{request.title}\'')

                # clear the playback event
                self._playback_event.clear()

                # play the request
                self._client.play(request.source, after=self.__onComplete__)

                # wait for the playback event to be set
                await self._playback_event.wait()

                log.debug(f'Finishing track \'{request.title}\'')

                # stop playing audio
                self._client.stop()

            except TimeoutError as error:
                log.error(error)
                await self._client.disconnect()
                self._client: Optional[VoiceClient] = None
                self._connection.clear()

            except Exception as error:
                log.error(error)
                self._connection.clear()
    

    async def skip(self, context: Context):
        if self._playback_event.is_set():
            pass
        else:
            pass
        self._playback_event.set()


    async def timeout(self, context: Context, *, length: Optional[str] = None):
        try:
            channel: discord.TextChannel = context._message.channel
            
            self.timeout = float(length) if length else None
            if length is None:
                await context.message.reply(f'Timeout disabled. Bot will not leave the voice channel after the queue is emptied.')
            else:
                await context.message.reply(f'Timeout set to {self.timeout} seconds. Bot will wait for this duration after the queue is empty before leaving the voice channel.')
        except ValueError as valueError:
            await channel.send(valueError)


    async def connect(self, context: Context, *, channel: str = None):
        """
        Joins the bot client to a voice channel.

        Parameters:
            - channel: The voice channel to join. Accepts a raw Channel ID or a Channel mention. Joins the channel of the command author if not provided.
        """

        state: Optional[VoiceState] = context.message.author.voice
        if not state:
            raise InvalidChannelError(None)

        channel: Optional[Union[VoiceChannel, StageChannel]] = state.channel
        if not channel:
            raise InvalidChannelError(None)
        else:
            self._channel: Optional[Union[VoiceChannel, StageChannel]] = state.channel
        try:
            self._client: Optional[VoiceClient] = await self._channel.connect()
            self._connection.set()
        except RuntimeError as error:
            log.error(error)
            await context.message.reply(error)


    async def disconnect(self, context: Context):
        """
        Disconnects the bot from the joined voice channel.
        """

        try:
            if not self._client:
                raise ConnectionError('Cannot disconnect: Not connected to begin with.')
            elif not self._client.is_connected():
                raise ConnectionError('Cannot disconnect: Not connected to begin with.')
            else:
                self._playback_event.set()
                await self._client.disconnect()
        except ConnectionError:
            raise
        except:
            await self._client.disconnect(force=True)
        finally:
            self._connection.clear()


    async def queue(self, context: Context, *, url: str = None, search: str = None, speed: str = None):
        """
        Add source media to the media queue.

        Parameters:
            - url: A URL link to a YouTube video to add to the queue.
            - search: Search terms to query YouTube for a source video.
        """

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
                # otherwise create list from data (a single entry)
                results: List[Dict[str, Any]] = entries if entries else list(data)
            except youtube_dl.utils.DownloadError as downloadError:
                await context.message.reply(downloadError)
                raise

            # get multiplier if speed was provided
            multiplier: Optional[float] = float(speed) if speed else None
            # assert the multiplier is within supported bounds
            multiplier: Optional[float] = multiplier if multiplier and multiplier > 0.5 and multiplier < 2.0 else None
            # create options string if multiplier is available
            options: Optional[str] = f'-filter:a \"atempo={multiplier}\"' if multiplier else None

            result: Optional[Dict[str, Any]] = results[0]
            if not result:
                await context.message.reply(f'No results found for {query}')
                return

            reference: Optional[str] = result.get('url')
            if not reference:
                await context.message.reply(f'Result was missing url.')
                return

            source: AudioSource = discord.FFmpegOpusAudio(reference, options=options)

            request: AudioRequest = AudioRequest(
                title=result.get('title'),
                url=result.get('url'),
                webpage_url=result.get('webpage_url'),
                channel=result.get('channel'),
                bitrate=result.get('abr'),
                thumbnail=result.get('thumbnail'),
                source=source,
            )
            await self._playback_queue.put(request)

            embed: discord.Embed = discord.Embed()
            embed.set_author(name=context.message.author.display_name, icon_url=context.message.author.avatar_url)
            embed.title = request.title
            embed.url = request.webpage_url
            embed.description = request.channel
            embed.set_image(url=request.thumbnail)
            embed.timestamp = context.message.created_at
            embed.color = discord.Colour.from_rgb(r=255, g=0, b=0)
            await context.message.channel.send(embed=embed)
        except:
            raise
        finally:
            pass


    async def play(self, context: Context, *, url: str = None, search: str = None, channel: str = None, speed: str = None):
        """
        Play audio from a YouTube video.

        Parameters:
            - url: A URL link to a YouTube video to add to the queue.
            - search: Search terms to query YouTube for a source video.
            - channel: The voice channel to join. Accepts a raw Channel ID or a Channel mention. Joins the channel of the command author if not provided.
        """

        try:
            # connect to the channel
            await self.connect(_client=context.client, _message=context.message, channel=channel)
        except discord.ClientException:
            # TODO:
            # VoiceClient.connect() - You are already connected to a voice channel.
            # VoiceClient.play() - Already playing audio or not connected.
            pass

        try:
            # queue the requested content
            await self.queue(_client=context.client, _message=context.message, url=url, search=search, speed=speed)
            # start the playback loop
            self.loop.create_task(self.__start__(context.client))
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


    async def nightcore(self, context: Context, *, url: str = None, search: str = None, channel: str = None, speed: str = '1.25'):
        """
        Play source media with a 1.25x speed filter applied.

        Parameters:
            - url: A URL link to a YouTube video to add to the queue.
            - search: Search terms to query YouTube for a source video.
        """
        await self.play(context, url=url, search=search, channel=channel, speed=speed)


class AudioRequest():
    """
    A request object for the bot to play.
    """

    def __init__(self, title: str, url: str, webpage_url: str, channel: str, bitrate: float, thumbnail: str, source: AudioSource):
        self._title: str = title
        self._url: str = url
        self._channel: str = channel
        self._bitrate: float = bitrate
        self._thumbnail: str = thumbnail
        self._source: AudioSource = source
        self._webpage_url: str = webpage_url

    @property
    def url(self) -> str:
        return self._url

    @property
    def webpage_url(self) -> str:
        return self._webpage_url

    @property
    def title(self) -> str:
        return self._title
    
    @property
    def channel(self) -> str:
        return self._channel
    
    @property
    def bitrate(self) -> float:
        return self._bitrate
    
    @property
    def thumbnail(self) -> str:
        return self._thumbnail

    @property
    def source(self) -> AudioSource:
        return self._source


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
