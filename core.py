from datetime import datetime, timezone
import logging
import re
from datetime import datetime, timezone
from logging import FileHandler, Formatter, Logger
from pathlib import Path
from typing import Dict, Optional

import discord
from discord import Client, Intents, Message
from pip import List
from context import Context
from router import HandlerError

from commandHandler import CommandHandler, MissingPrefixError
from providers.archiver import Archiver, Archive
from settings import Settings

log: Logger = logging.getLogger(__name__)

class Core(Client):

    def __init__(self) -> None:
        self._timestamp: datetime = datetime.now(tz=timezone.utc)
        self._settings: Settings = Settings()
        self._handler: CommandHandler = CommandHandler()
        self._archive: Archive = Archive()
        self._loggers: Dict[int, Logger] = dict()
        super().__init__(intents=Intents.all())

    async def on_ready(self):
        try:
            component_path: Path = self._settings.ux.components
            self._handler.load(component_path)
        except ValueError as error:
            log.warning(f"Failed to load: {error}")
        except HandlerError as error:
            log.warning(error)

        try:
            archive_path: Path = Path('./archive')
            self._archive.load(archive_path, self.guilds)
            await self._archive.fetch()
        except Exception:
            raise

        log.info("Ready!")

    async def on_message(self, message: Message):
        # if the provided message parameter was not a message
        if not isinstance(message, Message):
            return
        # log the message
        self.log_message(message)
        # archive the message
        self.archive_message(message)
        # if the message author is the bot
        if message.author.id == self.user.id:
            return
        try:
            context: Context = Context(
                self,
                message,
                self._settings,
                self._archive,
                self._timestamp,
                self._handler._packages,
            )
            # process the message
            await self._handler.handle(self._settings.ux.prefix, message, context=context)
        except MissingPrefixError:
            pass
        except HandlerError as error:
            log.error(error)
        except ValueError as error:
            log.error(error)

    def archive_message(self, message: Message):
        self._archive.write(message)

    def log_message(self, message: Message):
        # get the message author
        user: discord.User = message.author
        # get a logger for the channel
        logger: Optional[Logger] = self.get_logger(message.channel)
        # if a logger was found, log the message
        if logger:
            logger.info("%s#%s -> %s", user.name, user.discriminator, message.clean_content)

    def get_logger(self, channel: discord.TextChannel) -> Optional[Logger]:
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

