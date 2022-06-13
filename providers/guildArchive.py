import collections
import logging
from logging import Logger
from pathlib import Path
from typing import Dict, Iterator

import discord
from discord import Guild, Message

from providers.archiver import ChannelArchive

log: Logger = logging.getLogger(__name__)


class GuildArchive(collections.abc.MutableMapping):

    def __init__(self, guild: Guild, directory: Path) -> None:
        # set guild
        self._guild: Guild = guild
        # resolve the directory path
        self._directory: Path = directory.resolve()
        # get the path of the guild folder
        self._folder: Path = self._directory.joinpath(str(self._guild.id))
        # create the guild folder if it doesn't exist
        if not self._folder.exists(): self._folder.mkdir(parents=True, exist_ok=True)
        # create the archives dictionary
        self._archives: Dict[int, ChannelArchive] = {channel.id: ChannelArchive(channel, self._folder) for channel in self._guild.text_channels}

    def __setitem__(self, key: int, value: ChannelArchive) -> None:
        self._archives.__setitem__(key, value)
    
    def __getitem__(self, key: int) -> ChannelArchive:
        return self._archives.__getitem__(key)

    def __delitem__(self, key: int) -> None:
        self._archives.__delitem__(key)

    def __iter__(self) -> Iterator[int]:
        return self._archives.__iter__()

    def __len__(self) -> int:
        return self._archives.__len__()

    def __str__(self) -> str:
        return self._archives.__str__()

    def write(self, message: Message) -> None:
        self._archives[message.channel.id].write(message)

    async def fetch(self) -> None:
        for archive in self._archives.values():
            try:
                await archive.fetch()
            except discord.Forbidden as error:
                log.error(error)
