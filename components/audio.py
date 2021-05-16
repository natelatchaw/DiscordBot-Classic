import asyncio
from asyncio.events import AbstractEventLoop
from platform import platform
from typing import Any, Callable, Dict, List

import discord
from discord.channel import VoiceChannel
from discord.voice_client import VoiceClient
import youtube_dl
from discord.errors import ClientException
from discord.player import FFmpegAudio


class Audio():
    """
    Component description unavailable.
    """

    @property
    def voice_client(self) -> discord.VoiceClient:
        try:
            return self._voice_client
        except:
            return None
    @voice_client.setter
    def voice_client(self, voice_client: discord.VoiceClient):
        self._voice_client = voice_client

    def __init__(self):
        pass

    class AudioLogger():
        def debug(self, message):
            print('Audio.py', '<<DEBUG>>', message)

        def warning(self, message):
            print('Audio.py', '<<WARN>>', message)

        def error(self, message):
            print('Audio.py', '<<ERROR>>', message)

    async def connect(self, *, _client: discord.Client, _message: discord.Message, channel: str=None):
        try:
            # if the user specified a voice channel to use
            if channel:
                # convert the channel id string to an int
                channel_id: int = int(channel)
                # get a list of available voice channels
                channels: List[discord.VoiceChannel] = _message.guild.voice_channels
                # use the voice channel with a matching id
                voice_channel: discord.VoiceChannel = next((channel for channel in channels if channel.id == channel_id), None)
                if not voice_channel:
                    raise ValueError('The channel you specified is not valid for audio playback.')

            elif not _message.author.voice:
                raise ValueError('You must join a voice channel to use this command.')

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
        """
        try:
            if not self.voice_client:
                raise ConnectionError('Cannot disconnect: Not connected to begin with.')
            elif not self.voice_client.is_connected:
                raise ConnectionError('Cannot disconnect: Not connected to begin with.')
            else:
                await self.voice_client.disconnect()
        except ConnectionError:
            raise
        except:
            await self.voice_client.disconnect(force=True)

    async def play(self, *, _client: discord.Client, _message: discord.Message, url: str=None, channel: str=None):
        """
        *[BETA]* Play audio from a YouTube video.

        Parameters:
            - url: The url of the source video to play
        """
        try:
            await self.connect(_client=_client, _message=_message, channel=channel)
        except discord.ClientException:
            pass
        except Exception:
            raise

        try:
            bitrate: str = str(self.voice_client.channel.bitrate/1000)
            youtube_dl_options: Dict[str, Any] = {
                'format': 'bestaudio/best',
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'opus',
                        'preferredquality': bitrate,
                    },
                ],
                'logger': self.AudioLogger(),
                'progress_hooks': [

                ],
            }
            ffmpeg_options: Dict[str, str] = {
                'options': '-vn'
            }
            loop: AbstractEventLoop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL(youtube_dl_options).extract_info(url, download=False))

            location: str = data.get('url')
            title: str = data.get('title')
            bitrate: str = data.get('abr')
            thumbnail: str = data['thumbnails'][0]['url']
            
            audio_data: FFmpegAudio = discord.FFmpegPCMAudio(location, **ffmpeg_options)
            source = discord.PCMVolumeTransformer(audio_data)

            await _client.change_presence(activity=discord.Game(title))

            after: Callable[[Exception], Any] = lambda error: print(error) if error else None
            self.voice_client.play(source=source, after=after)

        except TypeError:
            # TODO: 
            # VoiceClient.play() - Source is not an AudioSource or after is not a callable.
            raise
        except asyncio.TimeoutError:
            # TODO:          
            # VoiceClient.connect() - Could not connect to the voice channel in time.
            raise
        except ClientException:
            # TODO:          
            # VoiceClient.connect() - You are already connected to a voice channel.
            # VoiceClient.play() - Already playing audio or not connected.
            raise
        except discord.opus.OpusNotLoaded:
            # TODO: 
            # VoiceClient.connect() - The opus library has not been loaded.
            # VoiceClient.play() - Source is not opus encoded and opus is not loaded.
            raise
        finally:
            await _client.change_presence(activity=None)
            await _message.delete()