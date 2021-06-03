import asyncio
from datetime import datetime, timezone
from typing import Type
import discord
import discord.ext
from discord.state import logging_coroutine
from router.error.handler import ComponentLookupError, HandlerError
from router.settings import Settings
from router.handler import Handler
from router.logger import Logger
from providers.archiver import Archiver
from router.error.configuration import ConfigurationError
from router.error.component import ComponentError

class ChannelLogger(Logger):

    def __init__(self, settings: Settings, guild: discord.Guild):
        super().__init__(settings)
        self.guild = guild

    async def print(self, *args):
        if not self.guild:
            return

        message = '\n'.join(args)
        try:
            # get the logging channel id from the config
            channel_id: int = self.settings.logging_channel
        except ConfigurationError:
            return
        # get the channel object from the channel id
        logging_channel = self.guild.get_channel(channel_id)
        if not isinstance(logging_channel, discord.TextChannel):
            return
        await logging_channel.send(f'{message}')

async def print_login_message(settings: Settings):
    if client.user:
        startup_message = f'Bot client {client.user.mention} initialized in {round((datetime.now() - instantiated_time).total_seconds(), 1)}s'
        for guild in client.guilds:
            logger: Logger = ChannelLogger(settings, guild)
            await logger.print(startup_message)

async def print_logout_message(settings: Settings):
    if client.user:
        shutdown_message = f'Bot client {client.user.mention} shutting down. Runtime: {round((datetime.now() - instantiated_time).total_seconds(), 1)}s'
        for guild in client.guilds:
            logger: Logger = ChannelLogger(settings, guild)
            await logger.print(shutdown_message)

async def archive_message(message: discord.Message):
    archiver: Archiver = Archiver(message.channel)
    # create a table for the current channel if it hasn't been created yet
    await archiver.create()
    # insert the current message into the archiver
    await archiver.insert(message)

try:
    # get the time the bot was initialized
    instantiated_time = datetime.now(tz=timezone.utc)
    # get the event loop
    loop = asyncio.get_event_loop()
    # initialize client object
    client = discord.Client(intents=discord.Intents.all())
    # initialize Settings
    settings = Settings('config')
    # initialize Handler
    handler = Handler()
    # load modules folder
    handler.load(settings.components)

    @client.event
    async def on_ready():
        # startup tasks
        print(f'{client.user.name} loaded in {settings.mode} mode.')
        await print_login_message(settings)

    @client.event
    async def on_message(message):
        # filter non-message objects
        if not isinstance(message, discord.Message):
            raise TypeError('Received an object that is not a message.')
        
        try:
            archiver: Archiver = Archiver(message.channel)
        except:
            archiver = None
        try:
            logger: ChannelLogger = ChannelLogger(settings, message.guild)
        except:
            logger = None

        # initialize optionals to pass to handler
        optionals: dict = {
            '_message': message,
            '_settings': settings,
            '_archiver': archiver,
            '_logger': logger,
            '_components': handler._components,
            '_client': client,
            '_features': handler.features,
            '_instantiated_time': instantiated_time,
        }
        
        try:
            # handle message
            await handler.process(settings.prefix, message.content, optionals=optionals)
        except ConfigurationError as configurationError:
            print(configurationError)
        except TypeError as typeError:
            # archive failed
            print(typeError)
        except HandlerError as handlerError:
            await message.channel.send(handlerError.internal_error)
        except Exception as exception:
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
    print(error.internal_error)
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
