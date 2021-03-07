import discord
from datetime import datetime
from .archiver import Archiver
from .configuration.uxstore import UXStore
import requests

class Handler():
    def __init__(self, client, uxStore):
        if not isinstance(client, discord.Client):
            raise TypeError('Invalid client parameter passed.')
        self._client = client
        self._uxStore = uxStore
        # create dictionary of archiver objects
        self._archivers = dict()

    async def process(self, message):
        # filter non-message objects
        if not isinstance(message, discord.Message):
            raise TypeError(f'Cannot process object that is not of type {type(discord.Message)}')

        # if an archiver instance hasn't been created for the current channel
        if message.channel.id not in self._archivers:
            # create an archiver instance
            archiver = Archiver(message.channel)
            # add the archiver instance to the archiver dict
            self._archivers[message.channel.id] = archiver
            print(f'Created archiver instance for channel {message.channel.id}')
        # if an archiver instance already exists for the current channel
        else:
            # get the archiver instance
            archiver = self._archivers[message.channel.id]
            print(f'Found archiver instance for channel {message.channel.id}')

        # create a table for the current channel if it hasn't been created yet
        await archiver.create()
        # insert the current message into the archiver
        await archiver.insert(message)

        # if the message doesn't ping the bot (i.e., is not a command)
        if not self._client.user in message.mentions:
            # print the message
            print(message.content)
            
        elif 'delete' in message.content:
            # try to get the owner id from the config
            try:
                # get the bot owner id
                bot_owner_id = str(self._uxStore.owner)
            # if an error occurred retrieving the owner id
            except ValueError as valueError:
                # set the bot owner id to None
                bot_owner_id = None

            # if the members intent is available
            if discord.Intents.members:
                # get the guild owner id
                server_owner_id = str(message.guild.owner.id)
            # otherwise
            else:
                # set the guild owner id to None
                server_owner_id = None

            # create user whitelist
            whitelist = [
                bot_owner_id,
                server_owner_id
            ]

            # if the message author is not in the whitelist
            if str(message.author.id) not in whitelist:
                await message.channel.send('You are not permitted to use this functionality.')
                raise ValueError(f'{message.author.id} is not a whitelisted user ID.')
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

        elif 'last year' in message.content:
            # try to get a message id from last year
            try:
                message_id, content = await archiver.get_last_year()
            # if a message could not be found
            except ValueError as valueError:
                # send the content of the error
                await message.channel.send(valueError)
                return
            # fetch the message from the channel via message id
            message = await message.channel.fetch_message(message_id)
            # create an embed containing the message's content
            embed = discord.Embed()
            embed.set_author(name=message.author.name, url=message.jump_url, icon_url=message.author.avatar_url)
            embed.title = message.content
            embed.timestamp = message.created_at
            # send the embed
            await message.channel.send(embed=embed)
                
        elif 'random' in message.content:
            message_id, attachment_url = await archiver.get_random_attachment_message()
            message = await message.channel.fetch_message(message_id)

            # check if the url's destination if actually a file
            headResponse = requests.head(attachment_url, allow_redirects=True)
            contentType = headResponse.headers.get('content-type')
            isImage = 'image' in contentType.lower()
            print(isImage)

            if isImage:
                print(attachment_url)
                getResponse = requests.get(attachment_url, allow_redirects=True)
                print(getResponse.history)
                attachment_url = getResponse.url
                print(attachment_url)

            embed = discord.Embed()
            embed.set_author(name=message.author.name, url=message.jump_url, icon_url=message.author.avatar_url)
            embed.title = message.jump_url
            embed.timestamp = message.created_at

            # if an Image
            if isImage:
                embed.set_image(url=attachment_url)
                await message.channel.send(embed=embed)

            # if not an Image
            else:
                await message.channel.send(attachment_url)
                await message.channel.send(embed=embed)

        archiver.close()
