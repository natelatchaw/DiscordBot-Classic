import collections
import logging
from logging import Logger
from pathlib import Path
from typing import Dict, Iterator, Optional

import discord
from discord import Client, Guild, Message

from providers.channelArchive import ChannelArchive
from providers.guildArchive import GuildArchive

log: Logger = logging.getLogger(__name__)


class ClientArchive(collections.abc.MutableMapping):
    
    def __init__(self, directory: Path, client: Client) -> None:
        # set client
        self._client: Client = client
        # resolve the provided directory path and append client directory
        self._directory: Path = directory.resolve().joinpath(str(self._client.user.id))
        # if the provided directory doesn't exist
        if not self._directory.exists(): self._directory.mkdir(parents=True, exist_ok=True)

        # initialize the archives directory
        self._archives: Dict[int, GuildArchive] = {guild.id: GuildArchive(self._directory, guild) for guild in self._client.guilds}

        
    def __setitem__(self, key: int, value: GuildArchive) -> None:
        self._archives.__setitem__(key, value)
    
    def __getitem__(self, key: int) -> GuildArchive:
        return self._archives.__getitem__(key)

    def __delitem__(self, key: int) -> None:
        self._archives.__delitem__(key)

    def __iter__(self) -> Iterator[int]:
        return self._archives.__iter__()

    def __len__(self) -> int:
        return self._archives.__len__()

    def __str__(self) -> str:
        return self._archives.__str__()


    def add(self, guild: Guild) -> None:
        # add the guild archive by ID
        self._archives[guild.id] = GuildArchive(self._directory, guild)
    
    def remove(self, guild: Guild) -> None:
        # remove the guild archive by ID
        del self._archives[guild.id]

    def save(self, message: Message):
        # get the message's guild
        guild: Optional[Guild] = message.guild
        # save the message
        if guild: self._archives[guild.id].save(message)

    async def fetch(self) -> None:
        for archive in self._archives.values():
            try:
                await archive.fetch()
            except Exception as error:
                log.error(error)
                raise
