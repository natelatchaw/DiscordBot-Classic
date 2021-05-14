import asyncio
from asyncio.events import AbstractEventLoop
from platform import platform
from typing import Any, Callable, Dict, List

import discord
import youtube_dl
from discord.errors import ClientException
from discord.player import FFmpegAudio


class Audio():
    """
    Component description unavailable.
    """

    def __init__(self):
        pass

    class AudioLogger():
        def debug(self, message):
            print('Audio.py', '<<DEBUG>>', message)

        def warning(self, message):
            print('Audio.py', '<<WARN>>', message)

        def error(self, message):
            print('Audio.py', '<<ERROR>>', message)

    async def play(self, *, _client: discord.Client, _message: discord.Message, url: str=None, channel: str=None):
        """
        *[BETA]* Play audio from a YouTube video.

        Parameters:
            - url: The url of the source video to play
        """
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

        except Exception as exception:
            raise

        try:
            reconnect: bool = True
            timeout: float = 3.0
            bitrate: str = str(voice_channel.bitrate/1000)
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

            # connect to the voice channel and get a VoiceClient
            voice_client: discord.VoiceClient = await voice_channel.connect(reconnect=reconnect, timeout=timeout)

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
            voice_client.play(source=source, after=after)

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
