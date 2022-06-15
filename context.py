from datetime import datetime
from typing import Dict

from discord import Client, Message
from router.packaging import Package

from providers.archiver import Archive
from settings import Settings


class Context:
    @property
    def client(self) -> Client:
        return self._client

    @property
    def message(self) -> Message:
        return self._message

    @property
    def settings(self) -> Settings:
        return self._settings

    @property
    def archive(self) -> Archive:
        return self._archive

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def packages(self) -> Dict[str, Package]:
        return self._packages

    def __init__(
        self,
        client: Client,
        message: Message,
        settings: Settings,
        archive: Archive,
        timestamp: datetime,
        packages: Dict[str, Package],
    ):
        self._client: Client = client
        self._settings: Settings = settings
        self._archive: Archive = archive
        self._message: Message = message
        self._timestamp: datetime = timestamp
        self._packages: Dict[str, Package] = packages
