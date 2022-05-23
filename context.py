from datetime import datetime
from typing import Dict
from discord import Client, Message
from providers.archiver import Archiver
from router.packaging import Package

from settings import Settings

class Context():

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
    def archiver(self) -> Archiver:
        return self._archiver

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def packages(self) -> Dict[str, Package]:
        return self._packages

    def __init__(self, client: Client, message: Message, settings: Settings, archiver: Archiver, timestamp: datetime, packages: Dict[str, Package]):
        self._client: Client = client
        self._settings: Settings = settings
        self._archiver: Archiver = archiver
        self._message: Message = message
        self._timestamp: datetime = timestamp
        self._packages: Dict[str, Package] = packages