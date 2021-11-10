import asyncio
from asyncio import events
from asyncio.events import AbstractEventLoop, Handle
from typing import Any, Dict, List
from queue import Queue
from typing_extensions import final

import discord
from discord import message
from discord.activity import Activity, BaseActivity, Game
from discord.channel import VoiceChannel
from discord.utils import get
from discord.voice_client import VoiceClient
import youtube_dl
from discord.errors import ClientException
from discord.player import AudioSource, FFmpegAudio


class Audio():
    """
    Component description unavailable.
    """

    class AudioLogger():
        def debug(self, message):
            print('Audio.py', '<<DEBUG>>', message)

        def warning(self, message):
            print('Audio.py', '<<WARN>>', message)

        def error(self, message):
            print('Audio.py', '<<ERROR>>', message)

    class AudioRequest():
        """
        A request object for the bot to play.
        """

        def __init__(self, title: str, url: str, webpage_url: str, channel: str, bitrate: float, thumbnail: str, source: AudioSource):
            self.title = title
            self.url = url
            self.webpage_url = webpage_url
            self.channel = channel
            self.bitrate = bitrate
            self.thumbnail = thumbnail
            self.source = source

    @property
    def request(self) -> AudioRequest:
        try:
            self._request
        except AttributeError:
            self._request = None
        finally:
            return self._request

    @request.setter
    def request(self, request):
        self._request = request

    @property
    def voice_client(self) -> discord.VoiceClient:
        try:
            return self._voice_client
        except:
            return None

    @voice_client.setter
    def voice_client(self, voice_client: discord.VoiceClient):
        self._voice_client = voice_client

    @property
    def loop(self) -> AbstractEventLoop:
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return asyncio.get_event_loop()

    @property
    def playback_event(self) -> asyncio.Event:
        try:
            if self._event is None:
                raise AttributeError()
        except AttributeError:
            self._event = asyncio.Event()
        finally:
            return self._event

    @playback_event.setter
    def playback_event(self, event: asyncio.Event):
        self._event = event

    @property
    def playback_queue(self) -> asyncio.Queue:
        try:
            if self._queue is None:
                raise AttributeError()
        except AttributeError:
            self._queue = asyncio.Queue()
        finally:
            return self._queue

    @playback_queue.setter
    def playback_queue(self, queue):
        self._queue = queue

    def __init__(self):
        pass

    async def start(self, _client: discord.Client):
        """
        The audio playback loop.
        This is used internally and should not be called as a command.
        """

        # if a request is currently being played
        if self.request is not None:
            return

        # loop while the voice client is connected
        while self.voice_client.is_connected():

            try:
                # define timeout
                timeout: float = 0.1 * 60
                # wait for a request to be added, or the timeout duration to expire
                self.request: self.AudioRequest = await asyncio.wait_for(self.playback_queue.get(), 3, loop=self.loop)

                # play the source content and set the event when done
                self.voice_client.play(
                    self.request.source, after=lambda _: self.loop.call_soon_threadsafe(self.playback_event.set))

                # wait for the event to be set before continuing
                await self.playback_event.wait()

                # reset the playback event
                self.playback_event = None

                # if the voice client is still playing audio
                if self.voice_client.is_playing():
                    # stop currently playing audio
                    self.voice_client.stop()

            # if the wait_for event elapses
            except asyncio.TimeoutError:
                print('Timed out')
                # disconnect
                await self.voice_client.disconnect()
                break

            # if already playing audio or not connected
            except discord.ClientException:
                break

            except Exception as exception:
                print(f'loop exception: {exception}')
                continue

        self.request = None
        await _client.change_presence(activity=None)

    async def connect(self, *, _client: discord.Client, _message: discord.Message, channel: str = None):
        """
        Joins the bot client to a voice channel.

        Parameters:
            - channel: The voice channel to join. Accepts a raw Channel ID or a Channel mention. Joins the channel of the command author if not provided.
        """
        try:
            # if the user specified a voice channel to use
            if channel:
                # convert the channel id string to an int
                channel_id: int = int(channel)
                # get a list of available voice channels
                channels: List[discord.VoiceChannel] = _message.guild.voice_channels
                # use the voice channel with a matching id
                voice_channel: discord.VoiceChannel = next(
                    (channel for channel in channels if channel.id == channel_id), None)
                if not voice_channel:
                    raise ValueError(
                        'The channel you specified is not valid for audio playback.')

            elif not _message.author.voice:
                raise ValueError(
                    'You must join a voice channel to use this command.')

            # if the user is in a voice channel
            elif _message.author.voice.channel:
                # use the voice channel the user is in
                voice_channel: discord.VoiceChannel = _message.author.voice.channel
                if not voice_channel:
                    raise ValueError('You must join a voice channel to use this command.')

            # if the user does not specify a voice channel and is not in a voice channel
            else:
                voice_channel = None
                if not voice_channel:
                    raise ValueError('You must join a voice channel to use this command.')

            reconnect: bool = True
            timeout: float = 3.0
            # connect to the voice channel and get a VoiceClient
            self.voice_client: discord.VoiceClient = await voice_channel.connect(reconnect=reconnect, timeout=timeout)
        except Exception:
            raise

    async def disconnect(self, *, _client: discord.Client, _message: discord.Message):
        """
        Disconnects the bot from the joined voice channel.
        """
        try:
            if not self.voice_client:
                raise ConnectionError('Cannot disconnect: Not connected to begin with.')
            elif not self.voice_client.is_connected:
                raise ConnectionError('Cannot disconnect: Not connected to begin with.')
            else:
                self.loop.call_soon_threadsafe(self.playback_event.set)
                await self.voice_client.disconnect()
        except ConnectionError:
            raise
        except:
            await self.voice_client.disconnect(force=True)

    async def queue(self, *, _client: discord.Client, _message: discord.Message, url: str = None, search: str = None, speed: str = None):
        """
        Add source media to the media queue.

        Parameters:
            - url: A URL link to a YouTube video to add to the queue.
            - search: Search terms to query YouTube for a source video.
        """
        try:
            if self.voice_client:
                #bitrate: str = str(self.voice_client.channel.bitrate/1000)
                pass
            else:
                #bitrate: str = '192'
                pass
            youtube_dl_options: Dict[str, Any] = {
                'format': 'bestaudio/best',
                'noplaylist': True,
                'age_limit': 18,
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'opus',
                        # 'preferredquality': bitrate,
                    },
                ],
                'logger': self.AudioLogger(),
                'progress_hooks': [

                ],
            }

            if url:
                data = await self.loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL(youtube_dl_options).extract_info(url, download=False))
            elif search:
                query = await self.loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL(youtube_dl_options).extract_info(f'ytsearch:{search}', download=False))
                videos = query.get('entries')
                data = videos.pop(0)
            else:
                return

            try:
                if speed is None: raise ValueError('No speed provided.')
                multiplier: float = float(speed)
                if multiplier < 0.5 or multiplier > 2.0: raise ValueError('Invalid speed setting.')
                options = f'-filter:a \"atempo={multiplier}\"'
            except ValueError:
                options = None

            source: AudioSource = discord.FFmpegOpusAudio(data.get('url'), options=options)

            request: self.AudioRequest = self.AudioRequest(
                title=data.get('title'),
                url=data.get('url'),
                webpage_url=data.get('webpage_url'),
                channel=data.get('channel'),
                bitrate=data.get('abr'),
                thumbnail=data.get('thumbnail'),
                source=source,
            )
            await self.playback_queue.put(request)

            activity: Game = Game(request.title)
            await _client.change_presence(activity=activity, status=None)

            embed: discord.Embed = discord.Embed()
            embed.set_author(name=_message.author.display_name, icon_url=_message.author.avatar_url)
            embed.title = request.title
            embed.url = request.webpage_url
            embed.description = request.channel
            embed.set_image(url=request.thumbnail)
            embed.timestamp = _message.created_at
            embed.color = discord.Colour.from_rgb(r=255, g=0, b=0)
            await _message.channel.send(embed=embed)
        except:
            raise
        finally:
            await _message.delete()

    async def skip(self, *, _client: discord.Client, _message: discord.Message):
        """
        Skips the currently playing track.
        """

        # set the event flag
        self.loop.call_soon_threadsafe(self.playback_event.set)

    async def play(self, *, _client: discord.Client, _message: discord.Message, url: str = None, search: str = None, channel: str = None, speed: str = None):
        """
        Play audio from a YouTube video.

        Parameters:
            - url: A URL link to a YouTube video to add to the queue.
            - search: Search terms to query YouTube for a source video.
            - channel: The voice channel to join. Accepts a raw Channel ID or a Channel mention. Joins the channel of the command author if not provided.
        """

        try:
            # connect to the channel
            await self.connect(_client=_client, _message=_message, channel=channel)
        except discord.ClientException:
            # TODO:
            # VoiceClient.connect() - You are already connected to a voice channel.
            # VoiceClient.play() - Already playing audio or not connected.
            pass

        try:
            # queue the requested content
            await self.queue(_client=_client, _message=_message, url=url, search=search, speed=speed)
            # start the playback loop
            self.loop.create_task(self.start(_client))
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

    async def nightcore(self, *, _client: discord.Client, _message: discord.Message, url: str = None, search: str = None, channel: str = None, speed: str = '1.25'):
        """
        Play source media with a 1.25x speed filter applied.

        Parameters:
            - url: A URL link to a YouTube video to add to the queue.
            - search: Search terms to query YouTube for a source video.
        """
        await self.play(_client=_client, _message=_message, url=url, search=search, channel=channel, speed=speed)
