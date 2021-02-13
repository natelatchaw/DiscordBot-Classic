import discord
from bot.core import Core

# initialize client object
client = discord.Client()
token = ''
prefix = ''

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

client.run(main.token)
