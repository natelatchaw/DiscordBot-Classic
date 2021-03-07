import discord
import discord.ext
from bot.core import Core
from bot.handler import Handler
from bot.archiver import Archiver

# initialize client object
client = discord.Client(intents=discord.Intents.all())

# initialize Core
main = Core()

# initialize Handler
handler = Handler(client, main._uxStore)

@client.event
async def on_ready():
    # startup tasks
    print(f'{client.user.name} loaded in {main.mode} mode.')

@client.event
async def on_message(message):
    # filter non-message objects
    if not isinstance(message, discord.Message):
        raise TypeError('Received an object that is not a message.')
    # if config is missing prefix
    elif not main.prefix:
        raise ValueError('No prefix has been set.')
    # handle message
    await handler.process(message)

try:
    client.run(main.token)
except ValueError as valueError:
    print(valueError)
except TypeError as typeError:
    print(typeError)