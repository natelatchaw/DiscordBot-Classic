import collections
import logging
from logging import Logger
from pathlib import Path
from typing import Dict, Iterator, List, Optional

from discord import Guild, Message

from providers.channelArchive import ChannelArchive
from providers.guildArchive import GuildArchive

log: Logger = logging.getLogger(__name__)

class Archive(collections.abc.MutableMapping):
    
    def __init__(self) -> None:
        # initialize the archive directory
        self._archives: Dict[int, GuildArchive] = dict()

    def load(self, directory: Path, guild: Guild) -> None:
        # resolve the provided directory path
        directory = directory.resolve()

        # if the provided directory doesn't exist
        if not directory.exists(): directory.mkdir(parents=True, exist_ok=True)

        # create and add the archive
        self._archives[guild.id] = GuildArchive(guild, directory)


    def load(self, directory: Path, guilds: List[Guild]) -> None:
        # resolve the provided directory path
        directory = directory.resolve()
        for guild in guilds: self.load(directory, guild)
        
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


    def write(self, message: Message):
        guild: Optional[Guild] = message.guild
        if guild: self._archives[guild.id].write(message)

    async def fetch(self) -> None:
        for archive in self._archives.values():
            try:
                await archive.fetch()
            except Exception as error:
                log.error(error)
                raise
