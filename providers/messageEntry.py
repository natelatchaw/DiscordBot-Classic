from __future__ import annotations

from datetime import datetime
from sqlite3 import Row
from typing import Any, List, Tuple, Type

from discord import Attachment, Message
from database.column import ColumnBuilder

from database.storable import Storable, TStorable
from database.table import Table, TableBuilder


class AttachmentEntry():

    @classmethod
    def fromAttachment(cls, attachment: Attachment) -> AttachmentEntry:
        return cls(attachment.id, attachment.url)

    @classmethod
    def fromRow(cls, row: Row) -> AttachmentEntry:
        return cls(row['ID'], row['URL'])

    def __init__(self, id: int, url: str) -> None:
        self._id: int = id
        self._url: str = url

    @property
    def id(self) -> int:
        return self._id

    @property
    def url(self) -> str:
        return self._url
        

class MessageEntry(Storable):

    def __init__(self, messageID: int, authorID: int, content: str, timestamp: datetime, attachments: List[Attachment] = list()) -> None:
        self._id: int = messageID
        self._author_id: int = authorID
        self._content: str = content
        self._timestamp: datetime = timestamp
        self._attachments: List[AttachmentEntry] = [AttachmentEntry.fromAttachment(attachment) for attachment in attachments]

    @property
    def id(self) -> int:
        return self._id

    @property
    def author_id(self) -> int:
        return self._author_id

    @property
    def content(self) -> str:
        return self._content
        
    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def attachments(self) -> List[AttachmentEntry]:
        return self._attachments
        

    @classmethod
    def fromMessage(cls, message: Message) -> MessageEntry:
        return cls(message.id, message.author.id, message.content, message.created_at, message.attachments)

    @classmethod
    def __table__(self) -> Table:
        # create a table builder
        t_builder: TableBuilder = TableBuilder()
        # set the table's name
        t_builder.setName('Messages')

        # create a column builder
        c_builder: ColumnBuilder = ColumnBuilder()
        # build columns
        t_builder.addColumn(c_builder.setName('ID').setType('INTEGER').isPrimary().isUnique().column())
        t_builder.addColumn(c_builder.setName('AuthorID').setType('INTEGER').column())
        t_builder.addColumn(c_builder.setName('Content').setType('TEXT').column())
        t_builder.addColumn(c_builder.setName('Timestamp').setType('TIMESTAMP').column())
        # build the table
        table: Table = t_builder.table()
        # return the table
        return table

    def __values__(self) -> Tuple[Any, ...]:
        # create a tuple with the corresponding values
        value: Tuple[Any, ...] = (self.id, self.author_id, self.content, self.timestamp)
        # return the tuple
        return value
        
    @classmethod
    def __from_row__(cls: Type[TStorable], row: Row) -> TStorable:
        # get the values from the row
        id: int = row['ID']
        author_id: int = row['AuthorID']
        content: str = row['Content']
        timestamp: datetime = row['Timestamp']
        # return the Metadata
        return MessageEntry(id, author_id, content, timestamp)
