import discord
import asyncio
from router.settings import Settings
from router.logger import Logger

class Delete():
    """
    Provides automated bulk message deletion functionality for text channels.
    """

    def __init__(self):
        pass

    async def delete(self, *, _message: discord.Message, _settings: Settings, _logger: Logger, limit: str=None, author: str=None):
        """
        Deletes messages from the text channel where the command is invoked. For example, for a limit of *n*, only the subset of the last *n* messages will be considered for deletion.

        Parameters:
            - limit: The number messages to operate on.
            - author: The user to target for message deletion.
        """

        # if the author provided a limit parameter
        if limit:
            try:
                # parse an integer from the string limit
                limit = int(limit)
            except ValueError as error:
                # log an error
                _logger.print(error)
                return
        # otherwise use the default limit of 100
        else:
            limit = 100

        if author:
            try:
                # parse an integer from the string author
                author = int(author)
            except ValueError as error:
                # log an error
                await _logger.print(error)
                return
        # otherwise use None
        else:
            author = None
        
        # try to get the owner id from the config
        try:
            # get the message owner id
            message_owner_id = str(_message.author.id)
        # if an error occurred retrieving the message owner id
        except ValueError:
            # set the message owner id to None
            message_owner_id = None

        # try to get the owner id from the config
        try:
            # get the bot owner id
            bot_owner_id = str(_settings.owner)
        # if an error occurred retrieving the owner id
        except ValueError:
            # set the bot owner id to None
            bot_owner_id = None

        # if the members intent is available
        if discord.Intents.members:
            # get the guild owner id
            server_owner_id = str(_message.guild.owner.id)
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
        if message_owner_id not in whitelist:
            await _logger.print('You are not authorized to delete messages.', f'For message {_message.jump_url}')
            raise ValueError(f'{_message.author.id} is not a whitelisted user ID.')
        # create empty list for messages to be added to
        messages = []
        # for each message in the channel's history
        async for message in _message.channel.history(limit=limit+1):
            # if the message is the delete command message
            if _message.id == message.id:
                # skip it
                continue
            # if the author was not specified
            if author is None:
                # add the message to the messages list
                messages.append(message)
            # if the message's author matches the provided author
            elif message.author.id == author:
                # add the message to the messages list
                messages.append(message)
        # get number of messages to be deleted
        message_count = len(messages)
        try:
            # delete every message in the messages list
            await _message.channel.delete_messages(messages)
        except discord.errors.Forbidden as error:
            await _logger.print(f'I am not authorized to delete messages in this server.', str(error))
            return
        except Exception as error:
            await _logger.print(str(error))
        # send a summary message
        summary_message = await _message.channel.send(f'{message_count} messages deleted.')
        # wait 3 seconds
        await asyncio.sleep(10)
        # delete the delete command
        await _message.delete()
        # delete the summary message
        await summary_message.delete()