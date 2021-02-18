import discord
from .archiver import Archiver

class Handler():
    def __init__(self, client):
        if not isinstance(client, discord.Client):
            raise TypeError('Invalid client parameter passed.')
        self._client = client

    async def process(self, message):
        if not isinstance(message, discord.Message):
            raise TypeError(f'Cannot process object that is not of type {type(discord.Message)}')

        archiver = Archiver(message.channel)
        await archiver.create()
        await archiver.insert(message)

        if not self._client.user in message.mentions:
            print(message.content)

        elif 'count' in message.content:
            count = await archiver.get_count()
            await message.channel.send(f'{count} messages archived in {message.channel.mention}')

        elif 'fetch' in message.content:
            await message.channel.send(f'Beginning download...')
            await archiver.fetch()
            count = await archiver.get_count()
            await message.channel.send(f'{count} messages archived in {message.channel.mention}')

        archiver.close()
