from logging import Logger
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from weakref import KeyedRef
import discord
from discord import TextChannel, DMChannel, Guild, Message
import sqlite3
from sqlite3 import Connection, Cursor, IntegrityError
import os
import re
import random
from datetime import datetime, timezone
from .snowflake import Snowflake
from .urlregex import urlRegex

log: Logger = logging.getLogger(__name__)

class Manipulator():
    def __init__(self, channel: TextChannel, directory: Path) -> None:
        if not isinstance(channel, TextChannel):
            raise TypeError(f'Archiving is not supported for {type(channel).__name__} types.')

        # resolve the directory path
        self._directory: Path = directory.resolve()
        # get the path of the channel database
        self._database: Path = self._directory.joinpath(str(channel.id) + '.db').resolve()
        # create the channel database if it doesn't exist
        if not self._database.exists(): self._database.touch(exist_ok=True)
        
        # connect to the database
        self._connection: Connection = sqlite3.connect(self._database)
        # set the connection's row factory
        self._connection.row_factory = sqlite3.Row
        # create the database cursor
        self._cursor: Cursor = self._connection.cursor()
        # assemble query
        query: str = '''
        CREATE TABLE IF NOT EXISTS MESSAGES (
            ID INTEGER UNIQUE PRIMARY KEY,
            AuthorID INTEGER,
            Content TEXT,
            Timestamp TIMESTAMP
        )
        '''
        # assemble query parameters
        parameters: Tuple = ()
        # execute the query with parameters
        self._cursor.execute(query, parameters)

    @property
    def oldest(self) -> Optional[datetime]:
        # assemble query
        query: str = '''
        SELECT * FROM MESSAGES
        ORDER BY ID ASC
        '''
        # assemble query parameters
        parameters: Tuple = ()
        #
        try:
            # execute the select statement with parameter injection
            self._cursor.execute(query, parameters)
            # fetch the first row
            message: sqlite3.Row = self._cursor.fetchone()
            # if no message was found, return None
            if message is None: return None
            # get the message ID
            id: int = message['ID']
            # return the timestamp
            return discord.utils.snowflake_time(id)
        except:
            raise

    @property
    def newest(self) -> Optional[datetime]:
        # assemble query
        query: str = '''
        SELECT * FROM MESSAGES
        ORDER BY ID DESC
        '''
        # assemble query parameters
        parameters: Tuple = ()
        #
        try:
            # execute the select statement with parameter injection
            self._cursor.execute(query, parameters)
            # fetch the first row
            message: sqlite3.Row = self._cursor.fetchone()
            # if no message was found, return None
            if message is None: return None
            # get the message ID
            id: int = message['ID']
            # return the timestamp
            return discord.utils.snowflake_time(id)
        except:
            raise


    def write(self, message: Message) -> None:
        # assemble query
        query: str = '''
        INSERT INTO MESSAGES VALUES (
            ?,
            ?,
            ?,
            ?
        )
        '''
        # assemble query parameters
        parameters: Tuple = (
            message.id,
            message.author.id,
            message.content,
            message.created_at
        
        )
        # try to insert and save message values
        try:
            # execute the insert statement with parameter injection
            self._cursor.execute(query, parameters)
            # save changes
            self._connection.commit()
        # catch integrity errors (UNIQUE constraints, etc.)
        except IntegrityError:
            raise


class Archiver2:
    def __init__(self, directory: Path) -> None:
        # resolve the directory path
        self._reference: Path = directory.resolve()
        # create the directory path
        if not self._reference.exists(): self._reference.mkdir(parents=True, exist_ok=True)
        # initialize manipulator dictionary
        self._manipulators: Dict[int, Manipulator] = dict()

        # store detected types for connect call
        types: int = sqlite3.PARSE_COLNAMES | sqlite3.PARSE_DECLTYPES

    def __create__(self, channel: discord.abc.Messageable):
        if not isinstance(channel, TextChannel):
            raise TypeError(f'Archiving is not supported for {type(channel).__name__} types.')
        
        # get the guild of the channel
        guild: Optional[Guild] = channel.guild
        # get the path of the guild's folder
        folder: Path = self._reference.joinpath(str(guild.id)).resolve()
        # if the guild folder doesn't exist
        if not folder.exists():
            # create the guild folder
            folder.mkdir(parents=True, exist_ok=True)
        # create and add manipulator
        self._manipulators[channel.id] = Manipulator(channel, folder)


    def __get_database__(self, channel: discord.abc.Messageable) -> Manipulator:
        if not isinstance(channel, TextChannel):
            raise TypeError(f'Archiving is not supported for {type(channel).__name__} types.')
        #
        if not self._manipulators.get(channel.id):
            #
            self.__create__(channel)
        #
        return self._manipulators.get(channel.id)


    def archive(self, message: Message) -> None:
        if not isinstance(message, Message):
            raise TypeError(f'Archiving is not supported for {type(message).__name__} types.')

        # get the TextChannel that the message was sent in
        channel: TextChannel = message.channel
        # if no existing manipulator exists for the channel
        if not self._manipulators.get(channel.id):
            # create 
            self.__get_database__(channel)
        # get the manipulator for the channel
        manipulator: Manipulator = self._manipulators[channel.id]
        # write the message
        manipulator.write(message)

    async def fetch(self, channel: TextChannel):
        # get the channel's manipulator
        manipulator: Manipulator = self.__get_database__(channel)
        # annotate message type
        message: Message
        
        # for each message in the channel history before the oldest recorded message 
        async for message in channel.history(limit=None, before=manipulator.oldest, oldest_first=False):
            logging.debug('Writing message %s to %s', message.id, manipulator._database.name)
            try:
                # write the message
                manipulator.write(message)
            except IntegrityError:
                pass

        # for each message in the channel history after the newest recorded message 
        async for message in channel.history(limit=None, after=manipulator.newest, oldest_first=True):
            logging.debug('Writing message %s to %s', message.id, manipulator._database.name)
            try:
                # write the message
                manipulator.write(message)
            except IntegrityError:
                pass



class Archiver:
    def __init__(self, channel: Optional[TextChannel]):
        if isinstance(channel, TextChannel):
            self._channel: TextChannel = channel
        elif isinstance(channel, DMChannel):
            raise TypeError(f'Provided channel is a {type(channel).__name__}. Archiving not supported.')
        else:
            raise TypeError("Provided channel is not a TextChannel.")

        # get the path of the data folder
        parent = os.path.abspath("data/")
        # if the data folder doesn't exist
        if not os.path.exists(parent):
            # create the data folder
            os.mkdir(parent)
        # append the database filename to the data folder path
        self._path = os.path.join(parent, f"{self._channel.guild.id}.db")
        # connect to the database
        self._connection = sqlite3.connect(self._path)
        # create the database cursor
        self._cursor = self._connection.cursor()

    async def create(self):
        # assemble create statment
        create_statement = f"""
            CREATE TABLE IF NOT EXISTS CHANNEL{self._channel.id} (
                MESSAGE_ID INTEGER UNIQUE PRIMARY KEY,
                CONTENT TEXT,
                AUTHOR_ID INTEGER,
                ATTACHMENTS TEXT
            )
        """
        # try to create table for channel
        try:
            # execute the create statement
            self._cursor.execute(create_statement)
        except Exception as exception:
            print(exception)

    async def insert(self, message):
        # filter non-message objects
        if not isinstance(message, discord.Message):
            raise TypeError(
                f"Message parameter was not of type {type(discord.Message)}."
            )

        # assemble INSERT statement
        insert_statement = f"""
            INSERT INTO CHANNEL{self._channel.id} VALUES(
                ?,
                ?,
                ?,
                ?
            )
        """
        # find all urls in the message content
        attachmentList = re.findall(urlRegex, message.content)
        # for each attachment in the message
        for attachment in message.attachments:
            # add the attachment to the attachment list
            attachmentList.append(attachment.url)
        # concatenate the attachment urls
        attachmentCSV = ",".join(attachmentList)
        # create values tuple
        values = (message.id, message.content, message.author.id, attachmentCSV)
        # try to insert and save message values
        try:
            # execute the insert statement with parameter injection
            self._cursor.execute(insert_statement, values)
            # save changes
            self._connection.commit()
        # catch integrity errors (UNIQUE constraints, etc.)
        except sqlite3.IntegrityError as integrityError:
            ##print(f'Message {message.id}: {integrityError.args}')
            pass

    async def select(self, columns: List[str] = ["MESSAGE_ID"]):
        select_statement: str = f"""
            SELECT {', '.join(columns)} FROM CHANNEL{self._channel.id}
        """
        self._cursor.execute(select_statement)
        # fetch the all rows
        return self._cursor.fetchall()

    async def fetch(self, limit: Optional[int] = None) -> None:
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

        try:
            # iterate through all channel messages older than oldest message in database (if available)
            async for message in self._channel.history(
                limit=limit, before=oldest_message_snowflake
            ):
                await self.insert(message)
            # iterate through all channel messages newer than newest message in database (if available)
            async for message in self._channel.history(
                limit=limit, after=newest_message_snowflake
            ):
                await self.insert(message)
        except discord.errors.Forbidden:
            raise Exception(f"Missing access for channel #{self._channel.name}")

    async def get_oldest(self) -> Optional[int]:
        query: str = f"""
            SELECT MESSAGE_ID FROM CHANNEL{self._channel.id}
            ORDER BY MESSAGE_ID ASC
            LIMIT 1
        """
        parameters: Tuple = ()
        self._cursor.execute(query, parameters)
        entries: List[Any] = self._cursor.fetchall()
        try:
            return int(entries[0])
        except:
            return None

    async def get_newest(self):
        query: str = f"""
            SELECT MESSAGE_ID FROM CHANNEL{self._channel.id}
            ORDER BY MESSAGE_ID DESC
            LIMIT 1
        """
        parameters: Tuple[Any] = ()
        self._cursor.execute(query, parameters)
        entries: List[Any] = self._cursor.fetchall()
        try:
            return int(entries[0])
        except:
            return None

    async def get_messages(self, *, member: discord.User = None) -> List:
        query: str = f"""
            SELECT * FROM CHANNEL{self._channel.id}
        """
        parameters: Tuple = ()

        if member:
            query = f"{query} WHERE AUTHOR_ID = :member_id"
            parameters = member.id

        self._cursor.execute(query, parameters)
        entries: List[Any] = self._cursor.fetchall()
        return entries

    async def get_count(self, *, member: discord.User = None):
        # assemble select statement
        select_statement = f"""
            SELECT * FROM CHANNEL{self._channel.id}
        """
        # if member is not none
        if member is not None:
            # add where clause
            select_statement = " ".join(
                [select_statement, f"WHERE AUTHOR_ID = {member.id}"]
            )

        # execute the select statement
        self._cursor.execute(select_statement)
        # get the length of the returned query
        count = len(self._cursor.fetchall())
        return count

    async def get_message(self, message_id):
        # assemble select statement
        select_statement = f"""
            SELECT MESSAGE_ID, AUTHOR_ID, CONTENT FROM CHANNEL{self._channel.id}
            WHERE MESSAGE_ID = {message_id}
        """
        # execute the SELECT statement
        self._cursor.execute(select_statement)
        # fetch all results
        entries = self._cursor.fetchall()
        # if no entries are available
        if len(entries) == 0:
            raise ValueError("No entries found matching your criteria.")
        # get the message id, author id and message content from first entry
        message_id, author_id, content = entries.pop()
        return message_id, author_id, content

    async def get_message_from_date(
        self, month: int, day: int, year: int, tzinfo: timezone = timezone.utc
    ):
        # get starting timestamp
        start_timestamp = datetime(year, month, day, 0, 0, 0, tzinfo=tzinfo)
        # get ending timestamp
        end_timestamp = datetime(year, month, day, 23, 59, 59, tzinfo=tzinfo)
        # get starting snowflake
        start_snowflake = Snowflake.from_timestamp(start_timestamp)
        # get ending snowflake
        end_snowflake = Snowflake.from_timestamp(end_timestamp)
        # assemble select statement
        select_statement = f"""
            SELECT MESSAGE_ID, CONTENT FROM CHANNEL{self._channel.id}
            WHERE MESSAGE_ID BETWEEN {start_snowflake} AND {end_snowflake}
        """
        # execute the SELECT statement
        self._cursor.execute(select_statement)
        # fetch all results
        entries = self._cursor.fetchall()
        # if no entries are available
        if len(entries) == 0:
            raise ValueError("No entries found matching your criteria.")
        # filter out entries with empty content strings
        entries = [entry for entry in entries if entry[1]]
        # select a random entry
        message_id, content = random.choice(entries)
        return message_id, content

    async def get_random_youtube_link(self):
        select_statement = f"""
            SELECT MESSAGE_ID, ATTACHMENTS FROM CHANNEL{self._channel.id}
        """
        # execute the SELECT statement
        self._cursor.execute(select_statement)
        # fetch all results
        entries = self._cursor.fetchall()
        # if no entries are available
        if len(entries) == 0:
            raise ValueError("No entries found matching your criteria.")
        # filter out entries with empty attachment strings
        entries = [entry for entry in entries if entry[1]]
        # get all attachments with youtube in the URL
        entries = [entry for entry in entries if "youtube" in entry[1]]
        # select a random entry
        _, attachments = random.choice(entries)
        # attachments may be a CSV string with multiple URLs, split it and concatenate with newline
        attachment_urls = attachments.split(",")
        # return a random url
        attachment_url = random.choice(attachment_urls)
        # return the author id and url
        return attachment_url

    async def get_random_attachment_message(self):
        select_statement = f"""
            SELECT MESSAGE_ID, ATTACHMENTS FROM CHANNEL{self._channel.id}
        """
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
        attachment_urls = attachments.split(",")
        # return a random url
        attachment_url = random.choice(attachment_urls)
        # return the author id and url
        return message_id, attachment_url

    def close(self):
        self._connection.close()
