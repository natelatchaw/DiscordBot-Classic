"""
Contains components for long term data management and storage.
"""

import io
import logging
import sqlite3
from datetime import datetime, timezone
from logging import Logger
from random import Random
from typing import Dict, List, Optional, Tuple

import discord
from context import Context
from discord import Guild, Message, TextChannel, User
from providers.channelArchive import ChannelArchive

log: Logger = logging.getLogger(__name__)

class Archive():
    """
    Provides functionality for querying the local message database.
    """

    def __init__(self, *args, **kwargs):
        self._archivers = dict()


    async def count(self, context: Context):
        """
        Retrieves the total number of messages stored in the local message database.

        Parameters:
            - user: Specify a user to filter the messages by.
        """

        guild: Guild = context.message.guild
        channel: TextChannel = context.message.channel
        user: User = context.message.author

        try:
            mention: Optional[User] = context.message.mentions.pop(0)
            if mention: user = mention
        except IndexError:
            pass

        archive: ChannelArchive = context.archive[guild.id][channel.id]

        sql: str = '''
        SELECT * FROM Messages
        WHERE AuthorID = ?
        '''
        parameters: Tuple = (user.id, )

        archive._cursor.execute(sql, parameters)
        rows: List[sqlite3.Row] = archive._cursor.fetchall()
        count: int = len(rows)

        embed: discord.Embed = discord.Embed()
        embed.set_author(name=user.name, icon_url=user.avatar_url)
        embed.description = f'{count} messages sent in #{channel.name}'
        embed.timestamp = datetime.now(tz=timezone.utc)

        response: Message = await channel.send(embed=embed)


    async def distribution(self, context: Context, *, containing: str=None):
        """
        Generates a bar graph of messages contained in the local message database per user.

        Parameters:
            - containing: A string to filter messages by. Only messages containing this string will be included. 
        """

        import matplotlib.pyplot as pyplot
        import numpy
        from matplotlib.figure import Figure
        from matplotlib.pyplot import Axes
        from PIL import Image


        guild: Guild = context.message.guild
        channel: TextChannel = context.message.channel
        user: User = context.message.author

        archive: ChannelArchive = context.archive[guild.id][channel.id]

        data: Dict[str, Tuple[User, int]] = dict()

        query = containing if containing else ''

        member: User
        for member in guild.members:
            sql: str = '''
            SELECT * FROM Messages
            WHERE AuthorID = ?
            AND Content LIKE ?
            '''
            parameters: Tuple = (member.id, f'%{query}%')
            archive._cursor.execute(sql, parameters)
            rows: List[sqlite3.Row] = archive._cursor.fetchall()
            data[member.id] = (member, len(rows))

        embed: discord.Embed = discord.Embed()
        embed.set_author(name=user.name, icon_url=user.avatar_url)
        embed.title = f'Message Distribution for messages containing \"{containing}\"' if containing else f'Message Distribution'
        embed.timestamp = datetime.now(tz=timezone.utc)

        # generate the figure and axes
        subplots: Tuple[Figure, Axes] = pyplot.subplots()
        figure: Figure = subplots[0]
        axes: Axes = subplots[1]
        # generate an evenly spaced range by the length of the data dict
        y_positions = numpy.arange(len(data))
        # get the message count from the data
        values: List[int] = [pair[1] for pair in data.values()]
        # create a horizontal bar plot
        axes.barh(y_positions, values, align='center')
        # set the y ticks at the calculated positions
        axes.set_yticks(y_positions)
        # set the y tick labels to the members list
        axes.set_yticklabels([pair[0].name for pair in data.values()])
        # invert the y axis to be horizontal
        axes.invert_yaxis()
        # turn on the grid
        axes.grid('on')
        # set the x axis label
        axes.set_xlabel('Messages')

        # create a buffer
        buffer: io.BytesIO = io.BytesIO()
        # save the figure to the buffer
        pyplot.savefig(buffer)
        # seek to beginning of buffer
        buffer.seek(0)

        # register the file with the discord library
        file = discord.File(buffer, filename="image.png")
        # add the image to the embed
        embed.set_image(url=f'attachment://image.png')
        # send the file and embed
        await channel.send(file=file, embed=embed)
        
    async def random(self, context: Context):
        """
        Retreives a random message attachment from the local message database.
        """

        guild: Guild = context.message.guild
        channel: TextChannel = context.message.channel
        user: User = context.message.author

        archive: ChannelArchive = context.archive[guild.id][channel.id]

        sql: str = '''
        SELECT * FROM Attachments
        '''
        parameters: Tuple = ()
        archive._cursor.execute(sql, parameters)
        rows: List[sqlite3.Row] = archive._cursor.fetchall()
        index: int = Random().randint(0, len(rows) - 1)
        row: sqlite3.Row = rows[index]
        messageID: int = row['MessageID']

        message: Message = await channel.fetch_message(messageID)
        attachment: discord.Attachment = message.attachments.pop(0)

        embed = discord.Embed()
        embed.set_author(name=message.author.name, url=message.jump_url, icon_url=message.author.avatar_url)
        embed.title = message.jump_url
        embed.timestamp = message.created_at
        embed.set_image(url=attachment.proxy_url)
        
        await channel.send(embed=embed)
