import discord
from bot.core import Core

# initialize client object
client = discord.Client()

# initialize Core
main = Core('production')
main.prefix = '/'

@client.event
async def on_ready():
    # startup tasks
    print('ready')

@client.event
async def on_message(message):
    if not isinstance(message, discord.Message):
        raise TypeError('Received an object that is not a message.')
    elif not main.prefix:
        raise ValueError('No prefix has been set.')
    else:
        # handle message
        print(message.content)

try:
    client.run(main.token)
except ValueError as valueError:
    print(valueError)
except TypeError as typeError:
    print(typeError)