from datetime import datetime, timezone
import time
import re
import os
import discord
import requests
import matplotlib.pyplot as pyplot
import numpy
from router.settings import Settings
#from router.archiver import Archiver
from router.logger import Logger

class Archive():
    """
    Provides functionality for querying the local message database.
    """

    def __init__(self):
        self._archivers = dict()

    async def fetch(self, *, _message: discord.Message, _settings: Settings, _archiver: Archiver, _logger: Logger):
        """
        Scans the message content of a text channel and copies data to the local message database.
        """
        message_reference = await _message.channel.send(f'Beginning download...')
        # record the time before fetch is run
        start_time = datetime.now()
        await _archiver.fetch()
        # record the time after fetch is run
        end_time = datetime.now()
        # calculate the time elapsed
        delta_time = end_time - start_time
        await message_reference.edit(content=f'{_message.channel.mention} archive updated in {round(delta_time.total_seconds(), 1)}s')
        try:
            # delete the command message
            await _message.delete()
        except discord.errors.Forbidden as error:
            await _logger.print(f'Could not delete command message {_message.id}', str(error))

    async def count(self, *, _message: discord.Message, _settings: Settings, _archiver: Archiver, _logger: Logger, user=None):
        """
        Retrieves the total number of messages stored in the local message database.

        Parameters:
            - user: Specify a user to filter the messages by.
        """
        if user:
            username = user.strip('@')
            for mentioned_member in _message.mentions:
                if mentioned_member.name == username:
                    target_member = mentioned_member
        else:
            target_member = None
        count = await _archiver.get_count(member=target_member)
        await _message.channel.send(f'{count} messages archived in {_message.channel.mention}')

    async def get_message(self, *, _message: discord.Message, _settings: Settings, _archiver: Archiver, _logger: Logger, date: str):
        """
        Retrieves a message from the local message database.

        Parameters:
            - date: Specify the date from which to retrieve a message.
        """
        try:
            # split string by any non-integer characters
            date_string_parts: list(str) = re.split("[^0-9]", date)
            # if there are not 3 segments
            if len(date_string_parts) != 3:
                raise ValueError(f"Could not read date from {date}")
            # map the string date parts to integer date parts
            date_parts: list(int) = list(map(int, date_string_parts))
            # get message from date parts
            message_id, _ = await _archiver.get_message_from_date(date_parts[0], date_parts[1], date_parts[2])
        except ValueError as valueError:
            await _message.channel.send(valueError)
            return
        # fetch the message from the channel via message id
        _message = await _message.channel.fetch_message(message_id)
        # create an embed containing the message's content
        embed = discord.Embed()
        embed.set_author(name=_message.author.name, url=_message.jump_url, icon_url=_message.author.avatar_url)
        embed.title = _message.content
        embed.timestamp = _message.created_at
        # send the embed
        await _message.channel.send(embed=embed)

    async def distribution(self, *, _message: discord.Message, _settings: Settings, _archiver: Archiver, _logger: Logger, containing: str=None):
        """
        Generates a bar graph of messages contained in the local message database per user.

        Parameters:
            - containing: A string to filter messages by. Only messages containing this string will be included. 
        """
        timestamp: int = int(time.time())

        message_count = dict()
        for member in _message.channel.guild.members:
            member_messages = await _archiver.get_messages(member=member)
            if containing:
                member_messages = [_message for _message in member_messages if (containing in _message[1])]
            key = member.id
            value = len(member_messages)
            message_count[key] = value

        embed = discord.Embed()
        embed.set_author(name=_message.author.name, icon_url=_message.author.avatar_url)
        if containing:
            embed.title = f'Message Distribution for messages containing \"{containing}\"'
        else:
            embed.title = f'Message Distribution'
        embed.timestamp = _message.created_at

        # generate the figure and axes
        figure, axes = pyplot.subplots()
        # map list of member ids to list of usernames
        members = [_message.guild.get_member(key).name for key in message_count.keys()]
        # map count values to counts list
        counts = [value for value in message_count.values()]
        # generate an evenly spaced range by the length of the members list
        y_positions = numpy.arange(len(members))
        # create a horizontal bar plot
        axes.barh(y_positions, counts, align='center')
        # set the y ticks at the calculated positions
        axes.set_yticks(y_positions)
        # set the y tick labels to the members list
        axes.set_yticklabels(members)
        # invert the y axis to be horizontal
        axes.invert_yaxis()
        # turn on the grid
        axes.grid('on')
        # set the x axis label
        axes.set_xlabel('Messages')

        # get the path of the cache folder
        parent = os.path.abspath('cache/')
        # if the cache folder doesn't exist
        if not os.path.exists(parent):
            # create the cache folder
            os.mkdir(parent)
        # join the filename to the parent path
        path = os.path.join(parent, f'{timestamp}.png')
        # save the plot to the generated path
        pyplot.savefig(path)
        # register the file with the discord library
        file = discord.File(path, filename='image.png')
        # add the image to the embed
        embed.set_image(url=f'attachment://image.png')
        # send the file and embed
        await _message.channel.send(file=file, embed=embed)
        try:
            # delete the command message
            await _message.delete()
        except discord.errors.Forbidden as error:
            await _logger.print(f'Could not delete command message {_message.id}', str(error))
            

    async def lastyear(self, *, _message: discord.Message, _settings: Settings, _archiver: Archiver, _logger: Logger):
        """
        Retrieves a message in the local message database from one year ago, on this date.
        """
        # try to get a message id from last year
        try:
            # get the current datetime in UTC
            now = datetime.now(timezone.utc)
            # get message from now timestamp
            message_id, _ = await _archiver.get_message_from_date(now.month, now.day, now.year-1)
        # if a message could not be found
        except ValueError as valueError:
            # send the content of the error
            await _message.channel.send(valueError)
            return
        # fetch the message from the channel via message id
        _message = await _message.channel.fetch_message(message_id)
        # create an embed containing the message's content
        embed = discord.Embed()
        embed.set_author(name=_message.author.name, url=_message.jump_url, icon_url=_message.author.avatar_url)
        embed.title = _message.content
        embed.timestamp = _message.created_at
        # send the embed
        await _message.channel.send(embed=embed)
        try:
            # delete the command message
            await _message.delete()
        except discord.errors.Forbidden as error:
            await _logger.print(f'Could not delete command message {_message.id}', str(error))

    async def random(self, *, _message: discord.Message, _settings: Settings, _archiver: Archiver, _logger: Logger):
        """
        Retreives a random message attachment from the local message database.
        """
        retries = 1
        # loop until no error
        while True:
            # try to get a message id that exists in the channel
            try:
                message_id, attachment_url = await _archiver.get_random_attachment_message()
                _message = await _message.channel.fetch_message(message_id)

                # check if the url's destination if actually a file
                headResponse = requests.head(attachment_url, allow_redirects=True)
                contentType = headResponse.headers.get('content-type')
                if not contentType:
                    raise TypeError
                if not 'image' in contentType.lower():
                    raise TypeError
                else:
                    break
            # if the channel is missing a message with message id
            except discord.errors.NotFound:
                print(f'{retries} invalid message id(s) found. Retrying...')
                retries = retries + 1
                if retries >= 10:
                    await _message.channel.send(f'Could not find a valid attachment in {retries} tries.')
                    attachment_url = None
                    break
                else:
                    continue
            except TypeError:
                # retrieved image has broken link, loop again
                print('Found image link, but link appears to be broken.')
                pass
            # if get_random_attachment_message returns an empty list
            except ValueError:
                await _message.channel.send(f'No attachments found in the database. Have you run `{_settings.prefix}fetch`?')
                attachment_url = None
                break

        getResponse = requests.get(attachment_url, allow_redirects=True)
        attachment_url = getResponse.url

        embed = discord.Embed()
        embed.set_author(name=_message.author.name, url=_message.jump_url, icon_url=_message.author.avatar_url)
        embed.title = _message.jump_url
        embed.timestamp = _message.created_at
        embed.set_image(url=attachment_url)
        await _message.channel.send(embed=embed)
        try:
            # delete the command message
            await _message.delete()
        except discord.errors.Forbidden as error:
            await _logger.print(f'Could not delete command message {_message.id}', str(error))
