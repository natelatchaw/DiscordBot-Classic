import asyncio
from datetime import datetime
import discord
import discord.ext
from router.settings import Settings
from router.handler import Handler
from router.logger import Logger

async def print_login_message(settings: Settings):
    if client.user:
        startup_message = f'Bot client {client.user.mention} initialized in {round((datetime.now() - instantiated_time).total_seconds(), 1)}s'
        for guild in client.guilds:
            logger: Logger = Logger(settings, guild)
            await logger.print(startup_message)

async def print_logout_message(settings: Settings):
    if client.user:
        shutdown_message = f'Bot client {client.user.mention} shutting down. Runtime: {round((datetime.now() - instantiated_time).total_seconds(), 1)}s'
        for guild in client.guilds:
            logger: Logger = Logger(settings, guild)
            await logger.print(shutdown_message)

async def archive_message(message: discord.Message):
    ###archiver: Archiver = Archiver(message.channel)
    # create a table for the current channel if it hasn't been created yet
    ###await archiver.create()
    # insert the current message into the archiver
    ###await archiver.insert(message)
    pass

try:
    # get the time the bot was initialized
    instantiated_time = datetime.now()
    # get the event loop
    loop = asyncio.get_event_loop()
    # initialize client object
    client = discord.Client(intents=discord.Intents.all())
    # initialize Core
    settings = Settings()
    # initialize Handler
    handler = Handler()
    # load modules folder
    handler.load(settings.modules)

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
        # initialize optionals to pass to handler
        optionals: dict = {
            '_message': message,
            '_core': settings,
            ###'_archiver': Archiver(message.channel),
            '_logger': Logger(settings, message.guild),
            '_modules': handler._modules
        }
        try:
            # handle message
            await handler.process(settings.prefix, message.content, optionals=optionals)
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
    loop.run_until_complete(client.start(settings.token))
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
    loop.run_until_complete(print_logout_message(settings))
    loop.run_until_complete(client.close())
