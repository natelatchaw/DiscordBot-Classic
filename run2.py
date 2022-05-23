import logging
import re
import sys
from datetime import datetime, timezone
from logging import FileHandler, Formatter, Logger, StreamHandler
from pathlib import Path
from typing import Any, Dict, List

import discord
import discord.ext
from discord import Client, Intents, Message
from router import HandlerError
from router.handler import Handler, Package, Component, Command
from commandHandler import CommandHandler
from context import Context

from providers.archiver import Archiver
from settings import Settings

logger: Logger = logging.getLogger()
formatter: Formatter = Formatter('[%(asctime)s] [%(pathname)s:%(lineno)d] [%(levelname)s] %(message)s')
#formatter: Formatter = Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')

stdoutHandler: StreamHandler = StreamHandler(sys.stdout)
stdoutHandler.setFormatter(formatter)
stdoutHandler.setLevel(logging.DEBUG)
logger.addHandler(stdoutHandler)

fileHandler: FileHandler = FileHandler('./.log', encoding='utf-8')
fileHandler.setFormatter(formatter)
fileHandler.setLevel(logging.DEBUG)
logger.addHandler(fileHandler)

logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger('discord').setLevel(logging.INFO)
logging.getLogger(Handler.__name__).setLevel(logging.INFO)
logging.getLogger(Package.__name__).setLevel(logging.INFO)
logging.getLogger(Component.__name__).setLevel(logging.INFO)
logging.getLogger(Command.__name__).setLevel(logging.INFO)

logging.addLevelName(logging.DEBUG, 'DBG')
logging.addLevelName(logging.INFO, 'INF')
logging.addLevelName(logging.WARN, 'WRN')
logging.addLevelName(logging.ERROR, 'ERR')
logging.addLevelName(logging.FATAL, 'FTL')

log: Logger = logging.getLogger(__name__)

class Core(Client):

    @property
    def token(self) -> str | None:
        return self._settings.token.current
    
    @property
    def prefix(self) -> str | None:
        return self._settings.ux.prefix

    @property
    def optionals(self) -> Dict[str, Any]:
        self._archiver: Archiver = None
        return {
            '_client': client,
            '_settings': self._settings,
            '_archiver': self._archiver,
            '_packages': self._handler._packages,
            '_timestamp': self._timestamp,
        }

    def __init__(self) -> None:
        self._timestamp: datetime = datetime.now(tz=timezone.utc)
        self._settings: Settings = Settings()
        self._handler: CommandHandler = CommandHandler()
        self._loggers: Dict[int, Logger] = dict()
        super().__init__(intents=Intents.all())

    async def on_ready(self):
        path: Path | None = self._settings.ux.components
        if path: self._handler.load(path)
        log.info('Ready!')

    async def on_message(self, message: Message):
        # if the provided message parameter was not a message
        if not isinstance(message, Message): return
        # log the message        
        self.log_message(message)
        # if the message author is the bot
        if message.author.id == self.user.id: return
        # get a copy of the optionals
        optionals: Dict[str, Any] = self.optionals
        # add the message to the optionals
        optionals['message'] = message
        try:
            context: Context = Context(self, message, self._settings, self._archiver, self._timestamp, self._handler._packages)
            # process the message
            await self._handler.process(self.prefix, message, context=context)
        except HandlerError as error:
            raise
            logging.error(error)


    def log_message(self, message: Message):
        # get the message author
        user: discord.User = message.author
        # log the message
        self.get_logger(message.channel).info('%s#%s -> %s', user.name, user.discriminator, message.content)

    def get_logger(self, channel: discord.TextChannel) -> Logger | None:
        try:
            path: Path = Path(f'./logs/{channel.id}.log').resolve()
            if not path.parent.exists(): path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists(): path.touch(exist_ok=True)
            logger: Logger = self._loggers[channel.id]
        except KeyError:
            logger: Logger = logging.getLogger(str(channel.id))
            handler: FileHandler = FileHandler(path)
            formatter: Formatter = Formatter('[%(asctime)s] %(message)s')
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
        parameter_matches: List[str] = [re.sub(r'<@!', '', parameter_match) for parameter_match in parameter_matches]
        # strip any user mention strings down to the author's id (mobile)
        parameter_matches: List[str] = [re.sub(r'<@', '', parameter_match) for parameter_match in parameter_matches]
        # strip any voice channel mention strings down to the channel's id
        parameter_matches: List[str] = [re.sub(r'<#', '', parameter_match) for parameter_match in parameter_matches]
        return parameter_matches
        

client = Core()

try:
    client.loop.run_until_complete(client.start(client.token))
except KeyboardInterrupt:
    client.loop.run_until_complete(client.close())
finally:
    client.loop.close()

logging.info('Exiting...')
exit()
