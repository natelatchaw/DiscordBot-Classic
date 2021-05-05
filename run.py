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

try:
    # get the time the bot was initialized
    instantiated_time = datetime.now()

    # get the event loop
    loop = asyncio.get_event_loop()

    # initialize client object
    client = discord.Client(intents=discord.Intents.all())
    # initialize Core
    main = Core()

    # initialize Handler
    handler = Handler(client, main)

    @client.event
    async def on_ready():
        # startup tasks
        print(f'{client.user.name} loaded in {main.mode} mode.')
        await print_login_message(main)

    @client.event
    async def on_message(message):
        # filter non-message objects
        if not isinstance(message, discord.Message):
            raise TypeError('Received an object that is not a message.')
        # initialize optionals to pass to handler
        optionals: dict = {
            '_core': main,
            '_logger': Logger(main, message.guild)
        }
        # handle message
        await handler.process(message, optionals=optionals, archiver_key='_archiver', modules_key='_modules')

    # try to start the bot client
    loop.run_until_complete(client.start(main.token))
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
    loop.run_until_complete(print_logout_message(main))
    loop.run_until_complete(client.logout())
    loop.run_until_complete(client.close())
