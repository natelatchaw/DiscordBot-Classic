import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from shortcutHandler import Shortcut, ShortcutHandler
from parameterHandler import ParameterHandler
from loggers.message_logger import MessageLogger

import discord
import discord.ext
from router.error.configuration import ConfigurationError
from router.error.handler import HandlerError
from router.handler import Handler
from router.logger import Logger
from router.settings import Settings

from loggers.channel_logger import ChannelLogger
from providers.archiver import Archiver


async def print_login_message(settings: Settings):
    if client.user:
        startup_message = f'Bot client {client.user.mention} initialized in {round((datetime.now(tz=timezone.utc) - instantiated_time).total_seconds(), 1)}s'
        for guild in client.guilds:
            logger: Logger = ChannelLogger(settings, guild)
            await logger.print(startup_message)

async def print_logout_message(settings: Settings):
    if client.user:
        shutdown_message = f'Bot client {client.user.mention} shutting down. Runtime: {round((datetime.now(tz=timezone.utc) - instantiated_time).total_seconds(), 1)}s'
        for guild in client.guilds:
            logger: Logger = ChannelLogger(settings, guild)
            await logger.print(shutdown_message)

async def archive_message(message: discord.Message):
    archiver: Archiver = Archiver(message.channel)
    # create a table for the current channel if it hasn't been created yet
    await archiver.create()
    # insert the current message into the archiver
    await archiver.insert(message)

async def archive_channels(client: discord.Client):
    for guild in client.guilds:
        guild: discord.Guild = guild
        for text_channel in guild.text_channels:
            text_channel: discord.TextChannel = text_channel
            archiver: Archiver = Archiver(text_channel)
            try:
                await archiver.create()
                await archiver.fetch()
                print(f'#{text_channel.name} archived')
            except Exception as exception:
                print(f'#{text_channel.name} archive failed: {exception}')

try:
    # get the time the bot was initialized
    instantiated_time: datetime = datetime.now(tz=timezone.utc)
    # get the event loop
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

    # define discord client intents
    intents: discord.Intents = discord.Intents.all()
    # initialize discord client object
    client: discord.Client = discord.Client(intents=intents)

    # initialize settings data from configuration file
    settings: Settings = Settings('config')
    # get the components path reference defined in configuration
    components_path: Path = Path(settings.components)
    # initialize handler
    handler = ParameterHandler()
    # load modules folder
    handler.load(components_path)

    @client.event
    async def on_ready():
        # startup tasks
        print(f'{client.user.name} loaded in {settings.mode} mode.')
        await print_login_message(settings)
        print(f'Beginning archive task.')
        await archive_channels(client)
        print(f'Archive task completed.')

    @client.event
    async def on_message(message: discord.Message):
        # filter non-message objects
        if not isinstance(message, discord.Message):
            raise TypeError('Received an object that is not a message.')
        
        try:
            archiver: Archiver = Archiver(message.channel)
        except:
            archiver = None
        try:
            channel_logger: ChannelLogger = ChannelLogger(settings, message.guild)
        except:
            channel_logger = None
        try:
            message_logger: MessageLogger = MessageLogger(settings, message.guild)
        except:
            message_logger = None

        # initialize optionals to pass to handler
        optionals: dict = {
            '_message': message,
            '_settings': settings,
            '_archiver': archiver,
            '_logger': channel_logger,
            '_components': handler._registrations,
            '_client': client,
            '_features': handler.features,
            '_instantiated_time': instantiated_time,
        }
        
        try:
            # handle message
            await handler.process(settings.prefix, message.content, optionals=optionals)
            await message_logger.print(message)
        except ConfigurationError as configurationError:
            print(configurationError)
        except TypeError as typeError:
            # archive failed
            print(typeError)
        except HandlerError as handlerError:
            await message.channel.send(handlerError.message)
        except Exception as exception:
            if settings.mode == 'development':
                raise
            if str(exception) is not None:
                # send error message
                await message.channel.send(exception)
            else:
                await message.channel.send('An unknown exception occurred.')
        finally:
            try:
                # archive message
                await archive_message(message)
            except Exception as exception:
                print(exception)
                
    # try to start the bot client
    loop.run_until_complete(client.start(settings.token))
# if TypeError or ValueError occurs
except ConfigurationError as error:
    #raise
    print(error.message)
# if program is interrupted in console
except KeyboardInterrupt as keyboardInterrupt:
    print(f'KeyboardInterrupt event occurred: {keyboardInterrupt}')
# if the client fails to login
except discord.errors.LoginFailure as loginFailure:
    print(f'Login failure occurred: {loginFailure}')
# if an unexpected error occurs
except:
    # throw it
    raise
# terminate gracefully
finally:
    # shutdown tasks
    loop.run_until_complete(print_logout_message(settings))
    loop.run_until_complete(client.close())
