import collections
import logging
from logging import Logger
from pathlib import Path
from typing import Dict, Iterator, Optional, Union

import discord
from discord import DMChannel, GroupChannel, Guild, Message, TextChannel
from discord.abc import GuildChannel, Messageable

from providers.clientArchive import ChannelArchive

log: Logger = logging.getLogger(__name__)


class GuildArchive(collections.abc.MutableMapping):

    def __init__(self, directory: Path, guild: Guild) -> None:
        # set guild
        self._guild: Guild = guild
        # resolve the provided directory path and append guild directory
        self._directory: Path = directory.resolve().joinpath(str(self._guild.id))
        # create the guild folder if it doesn't exist
        if not self._directory.exists(): self._directory.mkdir(parents=True, exist_ok=True)

        # create the archives dictionary
        self._archives: Dict[int, ChannelArchive] = {channel.id: ChannelArchive(self._directory, channel) for channel in self._guild.text_channels}


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
        

    def add(self, channel: GuildChannel) -> None:
        # make sure the provided channel inherits from Messageable
        if not isinstance(channel, Messageable):
            raise ValueError('Channel to archive must be Messageable.')
        # add the guild archive by ID
        self._archives[channel.id] = ChannelArchive(self._directory, channel)
    
    def remove(self, channel: GuildChannel) -> None:
        # remove the guild archive by ID
        del self._archives[channel.id]

    def save(self, message: Message) -> None:
        # get the message's channel
        channel: Optional[Union[TextChannel, DMChannel, GroupChannel]] = message.channel
        # save the message
        if channel: self._archives[channel.id].save(message)

    async def fetch(self) -> None:
        for archive in self._archives.values():
            try:
                await archive.fetch()
            except discord.Forbidden as error:
                log.error(f'#{archive._channel.name}: {error}')
