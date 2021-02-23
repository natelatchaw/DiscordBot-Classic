import discord
from datetime import datetime
from .archiver import Archiver
import requests

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
            
        elif 'delete' in message.content:
            if message.author.id != 196844910563950592: return
            messages = []
            async for message in message.channel.history():
                messages.append(message)
            await message.channel.delete_messages(messages)

        elif 'count' in message.content:
            count = await archiver.get_count()
            await message.channel.send(f'{count} messages archived in {message.channel.mention}')

        elif 'fetch' in message.content:
            message_reference = await message.channel.send(f'Beginning download...')
            # record the time before fetch is run
            start_time = datetime.now()
            await archiver.fetch()
            # record the time after fetch is run
            end_time = datetime.now()
            # calculate the time elapsed
            delta_time = end_time - start_time
            await message_reference.edit(content=f'{message.channel.mention} archive updated in {round(delta_time.total_seconds(), 1)}s')
                
        elif 'random' in message.content:
            message_id, attachment_url = await archiver.get_random_attachment_message()
            message = await message.channel.fetch_message(message_id)

            # check if the url's destination if actually a file
            cachedFile = requests.head(attachment_url, allow_redirects=True)
            contentType = cachedFile.headers.get('content-type')
            isFile = not ('text' or 'html' in contentType.lower())

            embed = discord.Embed()
            embed.set_author(name=message.author.name, url=message.jump_url, icon_url=message.author.avatar_url)
            embed.timestamp = message.created_at

            # if a file
            if isFile:
                embed.set_image(url=attachment_url)
                await message.channel.send(embed=embed)

            # if not a file
            else:
                embed.title = attachment_url
                print(contentType)
                await message.channel.send(attachment_url)
                await message.channel.send(embed=embed)

        archiver.close()
