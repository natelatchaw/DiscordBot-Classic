from __future__ import annotations

import datetime
from sqlite3 import Row
from typing import List

from discord import Attachment, Message


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
        

class MessageEntry():

    @classmethod
    def fromMessage(cls, message: Message) -> MessageEntry:
        return cls(message.id, message.author.id, message.content, message.created_at, message.attachments)

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
