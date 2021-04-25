import asyncio
from datetime import datetime
import discord
import discord.ext
from bot.core import Core
from bot.handler import Handler
from bot.archiver import Archiver
from bot.logging.logger import Logger

async def print_login_message():
    startup_message = f'Bot client {client.user.mention} initialized in {round((datetime.now() - instantiated_time).total_seconds(), 1)}s'
    for guild in client.guilds:
        await Logger.print(main, guild, startup_message)

async def print_logout_message():
    shutdown_message = f'Bot client {client.user.mention} shutting down. Runtime: {round((datetime.now() - instantiated_time).total_seconds(), 1)}s'
    for guild in client.guilds:
        await Logger.print(main, guild, shutdown_message)

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

    # initialize optionals to pass to handler
    optionals: dict = {
        '_core': main
    }

    @client.event
    async def on_ready():
        # startup tasks
        print(f'{client.user.name} loaded in {main.mode} mode.')
        await print_login_message()

    @client.event
    async def on_message(message):
        # filter non-message objects
        if not isinstance(message, discord.Message):
            raise TypeError('Received an object that is not a message.')
        # handle message
        await handler.process(message, optionals=optionals, archiver_key='_archiver')

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
    loop.run_until_complete(print_logout_message())
    loop.run_until_complete(client.logout())
    loop.run_until_complete(client.close())
