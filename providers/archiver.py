import discord
import sqlite3
import os
import re
import random
from datetime import datetime, timezone
from router.static.urlregex import urlRegex
from router.static.snowflake import Snowflake

class Archiver():

    def __init__(self, channel: discord.TextChannel):
        if isinstance(channel, discord.TextChannel):
            self._channel = channel
        elif isinstance(channel, discord.DMChannel):
            raise TypeError('Provided channel is a DMChannel. Archiving not supported.')
        else:
            raise TypeError('Provided channel is not a TextChannel.')

        # get the path of the data folder
        parent = os.path.abspath('data/')
        # if the data folder doesn't exist
        if not os.path.exists(parent):
            # create the data folder
            os.mkdir(parent)
        # append the database filename to the data folder path
        self._path = os.path.join(parent, f'{self._channel.guild.id}.db')
        # connect to the database
        self._connection = sqlite3.connect(self._path)
        # create the database cursor
        self._cursor = self._connection.cursor()

    async def create(self):
        # assemble create statment
        create_statement = f'''
            CREATE TABLE IF NOT EXISTS CHANNEL{self._channel.id} (
                MESSAGE_ID INTEGER UNIQUE PRIMARY KEY,
                CONTENT TEXT,
                AUTHOR_ID INTEGER,
                ATTACHMENTS TEXT
            )
        '''
        # try to create table for channel
        try:
            # execute the create statement
            self._cursor.execute(create_statement)
        except Exception as exception:
            print(exception)

    async def insert(self, message):
        # filter non-message objects
        if not isinstance(message, discord.Message):
            raise TypeError(f'Message parameter was not of type {type(discord.Message)}.')

        # assemble INSERT statement
        insert_statement = f'''
            INSERT INTO CHANNEL{self._channel.id} VALUES(
                ?,
                ?,
                ?,
                ?
            )
        '''
        # find all urls in the message content
        attachmentList = re.findall(urlRegex, message.content)
        # for each attachment in the message
        for attachment in message.attachments:
            # add the attachment to the attachment list
            attachmentList.append(attachment.url)
        # concatenate the attachment urls 
        attachmentCSV = ','.join(attachmentList)
        # create values tuple
        values = (
            message.id,
            message.content,
            message.author.id,
            attachmentCSV
        )
        # try to insert and save message values
        try:
            # execute the insert statement with parameter injection
            self._cursor.execute(insert_statement, values)
            # save changes
            self._connection.commit()
        # catch integrity errors (UNIQUE constraints, etc.)
        except sqlite3.IntegrityError as integrityError:
            print(f'Message {message.id}: {integrityError.args}')

    async def select(self):
        select_statement = f'''
            SELECT MESSAGE_ID FROM CHANNEL{self._channel.id}
        '''
        self._cursor.execute(select_statement)
        # fetch the all rows
        return self._cursor.fetchall()

    async def fetch(self, limit=None):
        # get message id of oldest message in database
        oldest_message_id = await self.get_oldest() or None
        try:
            oldest_message_snowflake = discord.utils.snowflake_time(oldest_message_id)
        except TypeError:
            oldest_message_snowflake = None

        # get message id of newest message in database
        newest_message_id = await self.get_newest() or None
        try:
            newest_message_snowflake = discord.utils.snowflake_time(newest_message_id)
        except TypeError:
            newest_message_snowflake = None

        # iterate through all channel messages older than oldest message in database (if available)
        async for message in self._channel.history(limit=limit, before=oldest_message_snowflake):
            await self.insert(message)

        # iterate through all channel messages newer than newest message in database (if available)
        async for message in self._channel.history(limit=limit, after=newest_message_snowflake):
            await self.insert(message)

    async def get_oldest(self):
        # assemble select statement
        select_statement = f'''
            SELECT MESSAGE_ID FROM CHANNEL{self._channel.id}
            ORDER BY MESSAGE_ID ASC
            LIMIT 1
        '''
        # execute the insert statement with parameter injection
        self._cursor.execute(select_statement)
        # fetch the first (and only) row
        oldest_entry = self._cursor.fetchone()
        try:
            # parse the retrieved message id to an integer
            oldest_message_id = int(oldest_entry[0])
        except:
            oldest_message_id = None
        # return the oldest message id
        return oldest_message_id

    async def get_newest(self):
        select_statement = f'''
            SELECT MESSAGE_ID FROM CHANNEL{self._channel.id}
            ORDER BY MESSAGE_ID DESC
            LIMIT 1
        '''
        self._cursor.execute(select_statement)
        # fetch the first (and only) row
        newest_entry = self._cursor.fetchone()
        try:
            # parse the retrieved message id to an integer
            newest_message_id = int(newest_entry[0])
        except:
            newest_message_id = None
        # return the newest message id
        return newest_message_id

    async def get_messages(self, *, member: discord.User = None):
        # assemble select statement
        select_statement = f'''
            SELECT * FROM CHANNEL{self._channel.id}
        '''
        # if member is not none
        if member is not None:
            # add where clause
            select_statement = ' '.join([select_statement, f'WHERE AUTHOR_ID = {member.id}'])

        # execute the select statement
        self._cursor.execute(select_statement)
        # get the length of the returned query
        return self._cursor.fetchall()

    async def get_count(self, *, member: discord.User = None):
        # assemble select statement
        select_statement = f'''
            SELECT * FROM CHANNEL{self._channel.id}
        '''
        # if member is not none
        if member is not None:
            # add where clause
            select_statement = ' '.join([select_statement, f'WHERE AUTHOR_ID = {member.id}'])

        # execute the select statement
        self._cursor.execute(select_statement)
        # get the length of the returned query
        count = len(self._cursor.fetchall())
        return count

    async def get_message(self, message_id):
        # assemble select statement
        select_statement = f'''
            SELECT MESSAGE_ID, AUTHOR_ID, CONTENT FROM CHANNEL{self._channel.id}
            WHERE MESSAGE_ID = {message_id}
        '''
        # execute the SELECT statement
        self._cursor.execute(select_statement)
        # fetch all results
        entries = self._cursor.fetchall()
        # if no entries are available
        if len(entries) == 0: raise ValueError("No entries found matching your criteria.")
        # get the message id, author id and message content from first entry
        message_id, author_id, content = entries.pop()
        return message_id, author_id, content

    async def get_message_from_date(self, month: int, day: int, year: int, tzinfo: timezone = timezone.utc):
        # get starting timestamp
        start_timestamp = datetime(year, month, day, 0, 0, 0, tzinfo=tzinfo)
        # get ending timestamp
        end_timestamp = datetime(year, month, day, 23, 59, 59, tzinfo=tzinfo)
        # get starting snowflake
        start_snowflake = Snowflake.from_timestamp(start_timestamp)
        # get ending snowflake
        end_snowflake = Snowflake.from_timestamp(end_timestamp)
        # assemble select statement
        select_statement = f'''
            SELECT MESSAGE_ID, CONTENT FROM CHANNEL{self._channel.id}
            WHERE MESSAGE_ID BETWEEN {start_snowflake} AND {end_snowflake}
        '''
        # execute the SELECT statement
        self._cursor.execute(select_statement)
        # fetch all results
        entries = self._cursor.fetchall()
        # if no entries are available
        if len(entries) == 0: raise ValueError("No entries found matching your criteria.")
        # filter out entries with empty content strings
        entries = [entry for entry in entries if entry[1]]
        # select a random entry
        message_id, content = random.choice(entries)
        return message_id, content

    async def get_random_youtube_link(self):
        select_statement = f'''
            SELECT MESSAGE_ID, ATTACHMENTS FROM CHANNEL{self._channel.id}
        '''
        # execute the SELECT statement
        self._cursor.execute(select_statement)
        # fetch all results
        entries = self._cursor.fetchall()
        # if no entries are available
        if len(entries) == 0: raise ValueError("No entries found matching your criteria.")
        # filter out entries with empty attachment strings
        entries = [entry for entry in entries if entry[1]]
        # get all attachments with youtube in the URL
        entries = [entry for entry in entries if 'youtube' in entry[1]]
        # select a random entry
        _, attachments = random.choice(entries)
        # attachments may be a CSV string with multiple URLs, split it and concatenate with newline
        attachment_urls = attachments.split(',')
        # return a random url
        attachment_url = random.choice(attachment_urls)
        # return the author id and url
        return attachment_url

    async def get_random_attachment_message(self):
        select_statement = f'''
            SELECT MESSAGE_ID, ATTACHMENTS FROM CHANNEL{self._channel.id}
        '''
        # execute the SELECT statement
        self._cursor.execute(select_statement)
        # fetch all results
        entries = self._cursor.fetchall()
        # filter out entries with empty attachment strings
        entries = [entry for entry in entries if entry[1]]
        # if no entries are available
        if len(entries) == 0:
            raise ValueError("No entries available.")
        # select a random entry
        message_id, attachments = random.choice(entries)
        # attachments may be a CSV string with multiple URLs, split it and concatenate with newline
        attachment_urls = attachments.split(',')
        # return a random url
        attachment_url = random.choice(attachment_urls)
        # return the author id and url
        return message_id, attachment_url

    def close(self):
        self._connection.close()