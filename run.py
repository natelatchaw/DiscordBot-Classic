import discord
from bot.core import Core

# initialize client object
client = discord.Client()

main = Core(client, '/', 'production')

@client.event
async def on_ready():
    # startup tasks
    print('ready')

@client.event
async def on_message(message):
    if not isinstance(message, discord.Message):
        raise TypeError('Received an object that is not a message.')
    # handle message

if main.token is not None:
    client.run(main.token)
