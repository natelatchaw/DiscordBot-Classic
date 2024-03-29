import collections
import logging
import sqlite3
from datetime import datetime
from logging import Logger
from pathlib import Path
from sqlite3 import Connection, Cursor, IntegrityError
from typing import Iterator, List, Optional, Tuple

import discord
from discord import Message, TextChannel

from providers.messageEntry import AttachmentEntry, MessageEntry

log: Logger = logging.getLogger(__name__)


class ChannelArchive(collections.abc.MutableMapping):

    def __init__(self, directory: Path, channel: TextChannel) -> None:
        # set channel
        self._channel: TextChannel = channel
        # resolve the directory path
        self._directory: Path = directory.resolve().joinpath(str(self._channel.id) + '.db')
        # create the channel database if it doesn't exist
        if not self._directory.exists(): self._directory.touch(exist_ok=True)
        
        # connect to the database
        self._connection: Connection = sqlite3.connect(self._directory)
        # set the connection's row factory
        self._connection.row_factory = sqlite3.Row
        # create the tables
        self.__create_messages__()
        self.__create_attachments__()
        

    def __setitem__(self, key: int, value: MessageEntry):
        # assemble query
        query: str = '''
        INSERT INTO Messages VALUES (
            ?, 
            ?, 
            ?, 
            ?
        )
        '''
        # assemble query parameters
        parameters: Tuple = (
            value.id,
            value.author_id,
            value.content,
            value.timestamp
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

        # assemble query
        query_a: str = '''
        INSERT INTO Attachments VALUES (
            ?,
            ?,
            ?
        )
        '''
        # assemble query parameters
        parameters_a: List[Tuple] = [(attachment.id, value.id, attachment.url) for attachment in value._attachments]
        # try to insert and save message values
        try:
            # execute the insert statement with parameter injection
            self._cursor.executemany(query_a, parameters_a)
            # save changes
            self._connection.commit()
        # catch integrity errors (UNIQUE constraints, etc.)
        except IntegrityError:
            raise

    def __getitem__(self, key: int) -> Optional[MessageEntry]:
        entry: Optional[MessageEntry] = None
        # assemble query
        query: str = '''
        SELECT * FROM Messages
        WHERE ID = ?
        '''
        # assemble query parameters
        parameters: Tuple = (
            key,
        )
        try:
            # execute the select statement with parameter injection
            self._cursor.execute(query, parameters)
            # fetch the first row
            message: sqlite3.Row = self._cursor.fetchone()
            # if no message was found, raise KeyError
            if message is None: raise KeyError(key)
            #
            entry = MessageEntry(message['ID'], message['AuthorID'], message['Content'], message['Timestamp'])
        # catch integrity errors (UNIQUE constraints, etc.)
        except IntegrityError:
            raise

        # assemble query
        query_a: str = '''
        SELECT * FROM Attachments
        WHERE MessageID = ?
        '''
        # assemble query parameters
        parameters_a: Tuple = (entry.id, )
        # try to insert and save message values
        try:
            # execute the insert statement with parameter injection
            self._cursor.execute(query_a, parameters_a)
            # fetch all rows
            attachments: List[sqlite3.Row] = self._cursor.fetchall()
            # add attachments to entry
            entry._attachments = [AttachmentEntry.fromRow(attachment) for attachment in attachments]
        # catch integrity errors (UNIQUE constraints, etc.)
        except IntegrityError:
            raise

        return entry
    
    def __delitem__(self, key: str) -> None:
        # assemble query
        query: str = '''
        DELETE * FROM Messages
        WHERE ID = ?
        '''
        # assemble query parameters
        parameters: Tuple = (
            key,
        )
        try:
            # execute the select statement with parameter injection
            self._cursor.execute(query, parameters)
            # save changes
            self._connection.commit()
        # catch integrity errors (UNIQUE constraints, etc.)
        except IntegrityError:
            raise

    def __iter__(self) -> Iterator[sqlite3.Row]:
        # assemble query
        query: str = '''
        SELECT * FROM Messages
        '''
        # assemble query parameters
        parameters: Tuple = (
        )
        try:
            # execute the select statement with parameter injection
            self._cursor.execute(query, parameters)
            # fetch rows
            messages: List[sqlite3.Row] = self._cursor.fetchall()
            # return the list's iter
            return messages.__iter__()            
        # catch integrity errors (UNIQUE constraints, etc.)
        except IntegrityError:
            raise

    def __len__(self) -> int:
        # assemble query
        query: str = '''
        SELECT * FROM Messages
        '''
        # assemble query parameters
        parameters: Tuple = (
        )
        try:
            # execute the select statement with parameter injection
            self._cursor.execute(query, parameters)
            # fetch rows
            messages: List[sqlite3.Row] = self._cursor.fetchall()
            # return the list's iter
            return messages.__len__()            
        # catch integrity errors (UNIQUE constraints, etc.)
        except IntegrityError:
            raise


    def __create_messages__(self) -> None:
        # create the database cursor
        self._cursor: Cursor = self._connection.cursor()
        # assemble query
        query: str = '''
        CREATE TABLE IF NOT EXISTS Messages (
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

    def __create_attachments__(self) -> None:
        # create the database cursor
        self._cursor = self._connection.cursor()
        # assemble query
        query: str = '''
        CREATE TABLE IF NOT EXISTS Attachments (
            ID INTEGER UNIQUE PRIMARY KEY,
            MessageID INTEGER,
            URL TEXT,
            FOREIGN KEY(MessageID) REFERENCES Messages(ID)
        )
        '''
        # assemble query parameters
        parameters: Tuple = ()
        # execute the query with parameters
        self._cursor.execute(query, parameters)


    def save(self, message: Message) -> None:
        entry = MessageEntry(message.id, message.author.id, message.content, message.created_at, message.attachments)
        self.__setitem__(message.id, entry)

    async def fetch(self) -> None:
        try:
            # annotate message type
            message: Message

            # for each message in the channel history before the oldest recorded message 
            async for message in self._channel.history(limit=None, before=self.oldest, oldest_first=False):
                logging.debug('Writing message %s to %s', message.id, self._directory.name)
                try:
                    # write the message
                    self.save(message)
                except IntegrityError:
                    pass

            # for each message in the channel history after the newest recorded message 
            async for message in self._channel.history(limit=None, after=self.newest, oldest_first=True):
                logging.debug('Writing message %s to %s', message.id, self._directory.name)
                try:
                    # write the message
                    self.save(message)
                except IntegrityError:
                    pass
        except discord.Forbidden:
            raise


    @property
    def oldest(self) -> Optional[datetime]:
        # assemble query
        query: str = '''
        SELECT * FROM Messages
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
        SELECT * FROM Messages
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
