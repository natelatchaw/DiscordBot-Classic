import abc
import collections
import logging
import os
import random
import re
import sqlite3
import struct
from datetime import datetime, timezone
from logging import Logger
from pathlib import Path
from sqlite3 import Connection, Cursor, IntegrityError
from typing import Any, Dict, Iterator, List, Optional, Tuple

import discord
from discord import DMChannel, Guild, Message, TextChannel

from .snowflake import Snowflake
from .urlregex import urlRegex


log: Logger = logging.getLogger(__name__)

class Entry():
    def __init__(self, messageID: int, authorID: int, content: str, timestamp: datetime) -> None:
        self._messageID: int = messageID
        self._authorID: int = authorID
        self._content: str = content
        self._timestamp: datetime = timestamp

    @property
    def messageID(self) -> int:
        return self._messageID

    @property
    def authorID(self) -> int:
        return self._authorID

    @property
    def content(self) -> str:
        return self._content
        
    @property
    def timestamp(self) -> datetime:
        return self._timestamp

class ChannelArchive(collections.abc.MutableMapping):

    def __setitem__(self, key: int, value: Entry):
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
            value.messageID,
            value.authorID,
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

    def __getitem__(self, key: int) -> Entry:
        # assemble query
        query: str = '''
        SELECT * FROM MESSAGES
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
            return Entry(message['ID'], message['AuthorID'], message['Content'], message['Timestamp'])
        # catch integrity errors (UNIQUE constraints, etc.)
        except IntegrityError:
            raise
    
    def __delitem__(self, key: str) -> None:
        # assemble query
        query: str = '''
        DELETE * FROM MESSAGES
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
        SELECT * FROM MESSAGES
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
        SELECT * FROM MESSAGES
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

    def __init__(self, channel: TextChannel, directory: Path) -> None:
        # set channel
        self._channel: TextChannel = channel
        # resolve the directory path
        self._directory: Path = directory.resolve()
        # get the path of the channel database
        self._database: Path = self._directory.joinpath(str(self._channel.id) + '.db').resolve()
        # create the channel database if it doesn't exist
        if not self._database.exists(): self._database.touch(exist_ok=True)
        
        # connect to the database
        self._connection: Connection = sqlite3.connect(self._database)
        # set the connection's row factory
        self._connection.row_factory = sqlite3.Row

        # create the table
        self.__create__()

    def __create__(self) -> None:
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

    async def fetch(self) -> None:
        try:
            # annotate message type
            message: Message

            # for each message in the channel history before the oldest recorded message 
            async for message in self._channel.history(limit=None, before=self.oldest, oldest_first=False):
                logging.debug('Writing message %s to %s', message.id, self._database.name)
                try:
                    # write the message
                    self.write(message)
                except IntegrityError:
                    pass

            # for each message in the channel history after the newest recorded message 
            async for message in self._channel.history(limit=None, after=self.newest, oldest_first=True):
                logging.debug('Writing message %s to %s', message.id, self._database.name)
                try:
                    # write the message
                    self.write(message)
                except IntegrityError:
                    pass
        except discord.Forbidden:
            raise

    def write(self, message: Message) -> None:
        entry = Entry(message.id, message.author.id, message.content, message.created_at)
        self.__setitem__(message.id, entry)
        return
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

