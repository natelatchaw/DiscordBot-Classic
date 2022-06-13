import asyncio
from datetime import datetime, timezone
import logging
from asyncio import Event, Queue, Task, TimeoutError
from asyncio.events import AbstractEventLoop
from logging import Logger
from pathlib import Path
from random import Random
from shlex import join
from sqlite3 import Connection, Row
from typing import Any, Dict, List, NoReturn, Optional, Tuple, Type, Union
from urllib.request import Request

import discord
from discord import Guild, TextChannel, User, Message
from matplotlib.image import thumbnail
import youtube_dl
from column import Column, ColumnBuilder
from context import Context
from discord import (ClientException, StageChannel, VoiceChannel, VoiceClient,
                     VoiceState)
from discord.player import AudioSource

from database import Database, Storable, TStorable
from table import Table, TableBuilder

log: Logger = logging.getLogger(__name__)


class Audio():
    """
    Component responsible for audio playback.
    """

    def __init__(self, *args, **kwargs):
        self._loop: Optional[AbstractEventLoop] = None
        self._connection: Event = Event()
        self._playback_event: Event = Event()
        self._playback_queue: Queue = Queue()
        self._timeout: Optional[float] = None
        self._client: Optional[VoiceClient] = None

        self.__setup__()

        task: Task[NoReturn] = asyncio.create_task(self.__start__())


    def __setup__(self) -> None:
        # create database instance
        self._database: Database = Database(Path('./archive/audio.db'))

    def __onComplete__(self, error: Optional[Exception]):
        """
        Called when a source completes in the audio loop.
        This is used internally and should not be called as a command.
        """
        # set the playback event
        self._playback_event.set()
        # log error if available
        if error:
            log.error(error)

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
                if self._client is None:
                    log.debug(f'No voice client available.')
                    log.debug('Resetting...')
                    # clear the connection event
                    self._connection.clear()
                    # restart the loop
                    continue

                log.debug(f'Waiting for next audio request')

                # get an audio request from the queue
                request: AudioRequest = await asyncio.wait_for(self._playback_queue.get(), self._timeout)

                log.debug(f'Beginning track \'{request.metadata.title}\'')

                # clear the playback event
                self._playback_event.clear()

                # play the request
                self._client.play(request.source, after=self.__onComplete__)

                # wait for the playback event to be set
                _: True = await self._playback_event.wait()

                log.debug(f'Finishing track \'{request.metadata.title}\'')

            except TimeoutError as error:
                log.error(error)
                if self._client:
                    await self._client.disconnect(force=True)
                    self._client: Optional[VoiceClient] = None
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
            metadata: Metadata = Metadata.from_dict(result, context.message.id, context.message.author.id)
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


    async def timeout(self, context: Context, *, length: Optional[str] = None):
        """
        Sets the number of seconds the bot should wait before disconnecting
        while idle in a voice channel.

        Parameters:
        - length: the number of seconds to wait
        """
        try:
            channel: discord.TextChannel = context._message.channel
            
            self._timeout = float(length) if length else None
            if length is None:
                await context.message.reply(f'Timeout disabled. Bot will not leave the voice channel after the queue is emptied.')
            else:
                await context.message.reply(f'Timeout set to {self._timeout} seconds. Bot will wait for this duration after the queue is empty before leaving the voice channel.')
        except ValueError as valueError:
            await channel.send(valueError)


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
            self._client: Optional[VoiceClient] = await self._channel.connect()
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
        if self._client:
            self._client.pause()
            return


    async def skip(self, context: Context):
        """
        Skips the current track.
        """
        if self._client:
            self._client.source = AudioSource()
            return

    
    async def stop(self, context: Context):
        """
        Stops audio playback.
        """
        if self._client:
            self._client.stop()
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


class Metadata(Storable):

    def __init__(self, id: int, user_id: int, video_id: str, title: str, channel: str, thumbnail: str, url: str) -> None:
        self._id: int = id
        self._user_id: int = user_id
        self._video_id: str = video_id
        self._title: str = title
        self._channel: str = channel
        self._thumbnail: str = thumbnail
        self._url: str = url

    @property
    def id(self) -> int:
        return self._id

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def video_id(self) -> str:
        return self._video_id

    @property
    def title(self) -> str:
        return self._title
    
    @property
    def channel(self) -> str:
        return self._channel
    
    @property
    def thumbnail(self) -> str:
        return self._thumbnail

    @property
    def url(self) -> str:
        return self._url

    def __table__(self) -> Table:
        # create a table builder
        t_builder: TableBuilder = TableBuilder()
        # set the table's name
        t_builder.setName('Metadata')

        # create a column builder
        c_builder: ColumnBuilder = ColumnBuilder()
        # create timestamp column
        t_builder.addColumn(c_builder.setName('ID').setType('INTEGER').isPrimary().isUnique().column())
        # create user ID column
        t_builder.addColumn(c_builder.setName('UserID').setType('INTEGER').column())
        # create video ID column
        t_builder.addColumn(c_builder.setName('VideoID').setType('TEXT').column())
        # create title column
        t_builder.addColumn(c_builder.setName('Title').setType('TEXT').column())
        # create channel column
        t_builder.addColumn(c_builder.setName('Channel').setType('TEXT').column())
        # create channel column
        t_builder.addColumn(c_builder.setName('Thumbnail').setType('TEXT').column())
        # create url column
        t_builder.addColumn(c_builder.setName('URL').setType('TEXT').column())
        
        # build the table
        table: Table = t_builder.table()
        # return the table
        return table

    def __values__(self) -> Tuple[Any, ...]:
        # create a tuple with the corresponding values
        value: Tuple[Any, ...] = (self.id, self.user_id, self.video_id, self.url, self.title, self.channel, self.thumbnail)
        # return the tuple
        return value

    @classmethod
    def from_dict(cls, dict: Dict[str, Any], snowflake: int, user_id: int):
        id: int = snowflake
        if not isinstance(id, int):
            raise TypeError(f'Message ID is not of type {type(int)}')

        user_id: int = user_id
        if not isinstance(user_id, int):
            raise TypeError(f'User ID is not of type {type(int)}')

        video_id: str = dict['id']
        if not isinstance(video_id, str):
            raise TypeError(f'Key \'id\' is not of type {type(str)}')
        
        title: str = dict['title']
        if not isinstance(title, str):
            raise TypeError(f'Key \'title\' is not of type {type(str)}')
        
        channel: str = dict['channel']
        if not isinstance(channel, str):
            raise TypeError(f'Key \'channel\' is not of type {type(str)}')
        
        thumbnail: str = dict['thumbnail']
        if not isinstance(channel, str):
            raise TypeError(f'Key \'thumbnail\' is not of type {type(str)}')

        url: str = dict['url']
        if not isinstance(url, str):
            raise TypeError(f'Key \'url\' is not of type {type(str)}')
        
        return Metadata(id, user_id, video_id, title, channel, thumbnail, url)
        
    @classmethod
    def __from_row__(cls: Type[TStorable], row: Row) -> TStorable:
        # Get ID value from the row
        id: int = row['ID']
        # Get UserID value from the row
        user_id: int = row['UserID']
        # Get VideoID value from the row
        video_id: str = row['VideoID']
        # Get URL value from the row
        url: str = row['URL']
        # Get Title value from the row
        title: str = row['Title']
        # Get Channel value from the row
        channel: str = row['Channel']
        # Get thumbnail value from the row
        thumbnail: str = row['Thumbnail']
        # return the Metadata
        return Metadata(id, user_id, video_id, url, title, channel, thumbnail)


class AudioRequest():
    """
    A request object for the bot to play.
    """

    def __init__(self, source: AudioSource, metadata: Metadata):
        self._metadata: Metadata = metadata
        self._source: AudioSource = source
    
    @property
    def metadata(self) -> Metadata:
        return self._metadata

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
