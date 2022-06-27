import logging
import re
from datetime import datetime, timezone
from logging import FileHandler, Formatter, Logger
from pathlib import Path
from typing import Dict, Optional, Union

import discord
from discord.abc import GuildChannel
from discord import (Client, DMChannel, GroupChannel, Intents, Member, Message,
                     TextChannel, User)
from pip import List
from router import HandlerError

from commandHandler import CommandHandler, MissingPrefixError
from context import Context
from providers.clientArchive import ClientArchive
from rateLimiter import RateLimiter
from settings import Settings

log: Logger = logging.getLogger(__name__)

class Core(Client):

    def __init__(self) -> None:
        self._timestamp: datetime = datetime.now(tz=timezone.utc)
        self._settings: Settings = Settings()
        self._limiter: RateLimiter = RateLimiter(self._settings)
        self._handler: CommandHandler = CommandHandler()
        self._loggers: Dict[int, Logger] = dict()
        super().__init__(intents=Intents.all())

    async def on_ready(self):
        self._archive: ClientArchive = ClientArchive(Path('./archive'), self)
        await self.__on_ready__()

    async def on_guild_channel_create(self, channel: GuildChannel):
        print('creating channel in archive....')
        self._archive[channel.guild.id].add(channel)
    
    async def on_guild_channel_delete(self, channel: GuildChannel):
        print('removing channel in archive....')
        self._archive[channel.guild.id].remove(channel)

    async def on_message(self, message: Message):
        await self.__on_message__(message)

    ################################################################################
    #                                                                              #
    #                                                                              #
    #                                                                              #
    ################################################################################


    async def __on_ready__(self):
        try:
            if not self._settings.client.data.components:
                raise HandlerError('No components directory provided.')
            self._handler.load(self._settings.client.data.components, extension='py', client=self, settings=self._settings)
            self._handler.addLimiter(self._limiter)
        except HandlerError as error:
            log.warning(error)

        try:
            archive_path: Path = Path('./archive')
            #for guild in self.guilds:
                #self._archive.load(archive_path, guild)
            await self._archive.fetch()
        except Exception:
            raise

        log.info("Ready!")

    async def __on_message__(self, message: Message):
        
        # if the provided message parameter was not a message
        if not isinstance(message, Message):
            return
        # log the message
        self.__log_message__(message)
        # archive the message
        self.__archive_message__(message)
        # if the message author is the bot
        if message.author.id == self.user.id:
            return
        try:
            prefix: Optional[str] = self._settings.for_guild(message.guild).ux.prefix
            context: Context = Context(
                self,
                message,
                self._settings,
                self._archive,
                self._timestamp,
                self._handler._packages,
            )
            # process the message
            if prefix: await self._handler.handle(prefix, message, context=context)
        except MissingPrefixError:
            pass
        except HandlerError as error:
            log.error(error)


    def __archive_message__(self, message: Message):
        self._archive.save(message)

    def __log_message__(self, message: Message):
        # get the message author
        user: Union[User, Member] = message.author
        # get a logger for the channel
        logger: Optional[Logger] = self.__get_logger__(message.channel)
        # if a logger was found, log the message
        if logger:
            logger.info("%s#%s -> %s", user.name, user.discriminator, message.clean_content)

    def __get_logger__(self, channel: Union[TextChannel, DMChannel, GroupChannel]) -> Optional[Logger]:
        logger: Optional[Logger] = None
        try:
            path: Path = Path(f"./logs/{channel.id}.log").resolve()
            if not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.touch(exist_ok=True)
            logger = self._loggers[channel.id]
        except KeyError:
            logger = logging.getLogger(str(channel.id))
            handler: FileHandler = FileHandler(path)
            formatter: Formatter = Formatter("[%(asctime)s] %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            self._loggers[channel.id] = logger
        finally:
            return logger

    def filter(self, parameter_matches: List[str]) -> List[str]:
        """
        A parameter match filter for the message handler.
        """
        # strip any user mention strings down to the author's id
        parameter_matches = [
            re.sub(r"<@!", "", parameter_match) for parameter_match in parameter_matches
        ]
        # strip any user mention strings down to the author's id (mobile)
        parameter_matches = [
            re.sub(r"<@", "", parameter_match) for parameter_match in parameter_matches
        ]
        # strip any voice channel mention strings down to the channel's id
        parameter_matches = [
            re.sub(r"<#", "", parameter_match) for parameter_match in parameter_matches
        ]
        return parameter_matches

