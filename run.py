import asyncio
from datetime import datetime
import discord
import discord.ext
from bot.core import Core
from bot.handler import Handler
from bot.archiver import Archiver
from bot.logger import Logger

async def print_login_message(core: Core):
    if client.user:
        startup_message = f'Bot client {client.user.mention} initialized in {round((datetime.now() - instantiated_time).total_seconds(), 1)}s'
        for guild in client.guilds:
            logger: Logger = Logger(core, guild)
            await logger.print(startup_message)

async def print_logout_message(core: Core):
    if client.user:
        shutdown_message = f'Bot client {client.user.mention} shutting down. Runtime: {round((datetime.now() - instantiated_time).total_seconds(), 1)}s'
        for guild in client.guilds:
            logger: Logger = Logger(core, guild)
            await logger.print(shutdown_message)

async def archive_message(message: discord.Message):
    archiver: Archiver = Archiver(message.channel)
    # create a table for the current channel if it hasn't been created yet
    await archiver.create()
    # insert the current message into the archiver
    await archiver.insert(message)

try:
    # get the time the bot was initialized
    instantiated_time = datetime.now()
    # get the event loop
    loop = asyncio.get_event_loop()
    # initialize client object
    client = discord.Client(intents=discord.Intents.all())
    # initialize Core
    core = Core()
    # initialize Handler
    handler = Handler()
    # load modules folder
    handler.load(core.modules)

    @client.event
    async def on_ready():
        # startup tasks
        print(f'{client.user.name} loaded in {core.mode} mode.')
        await print_login_message(core)

    @client.event
    async def on_message(message):
        # filter non-message objects
        if not isinstance(message, discord.Message):
            raise TypeError('Received an object that is not a message.')
        # initialize optionals to pass to handler
        optionals: dict = {
            '_message': message,
            '_core': core,
            '_archiver': Archiver(message.channel),
            '_logger': Logger(core, message.guild),
            '_modules': handler._modules
        }
        try:
            # handle message
            await handler.process(core.prefix, message.content, optionals=optionals)
        except ValueError:
            # no prefix configured
            pass
        except Exception as exception:
            # send error message
            await message.channel.send(exception)
        finally:
            # archive message
            await archive_message(message)
    # try to start the bot client
    loop.run_until_complete(client.start(core.token))
# if TypeError or ValueError occurs
except (TypeError, ValueError) as error:
    print(error)
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
    loop.run_until_complete(print_logout_message(core))
    loop.run_until_complete(client.close())
