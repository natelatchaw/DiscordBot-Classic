import discord
from datetime import datetime
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
            # record the time before fetch is run
            start_time = datetime.now()
            await archiver.fetch()
            # record the time after fetch is run
            end_time = datetime.now()
            # calculate the time elapsed
            delta_time = end_time - start_time
            await message.channel.send(f'{message.channel.mention} archive updated in {round(delta_time.total_seconds(), 1)}s')
        
        elif 'random' in message.content:
            attachment = await archiver.get_random_image()
            await message.channel.send(attachment)

        archiver.close()
