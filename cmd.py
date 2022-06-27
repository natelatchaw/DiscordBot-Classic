import asyncio
import logging
import sys
from logging import FileHandler, Formatter, Logger, StreamHandler

from router.handler import Handler

from commandHandler import CommandHandler
from settings import Settings

log: Logger = logging.getLogger(__name__)

# formatter: Formatter = Formatter('[%(asctime)s] [%(pathname)s:%(lineno)d] [%(levelname)s] %(message)s')
formatter: Formatter = Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
)

stdoutHandler: StreamHandler = StreamHandler(sys.stdout)
stdoutHandler.setFormatter(formatter)
stdoutHandler.setLevel(logging.DEBUG)
log.addHandler(stdoutHandler)

fileHandler: FileHandler = FileHandler("./.log", encoding="utf-8")
fileHandler.setFormatter(formatter)
fileHandler.setLevel(logging.DEBUG)
log.addHandler(fileHandler)

logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger("discord").setLevel(logging.INFO)
logging.getLogger(Handler.__name__).setLevel(logging.DEBUG)

logging.addLevelName(logging.DEBUG, "DBG")
logging.addLevelName(logging.INFO, "INF")
logging.addLevelName(logging.WARN, "WRN")
logging.addLevelName(logging.ERROR, "ERR")
logging.addLevelName(logging.FATAL, "FTL")


loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

settings: Settings = Settings()
handler: Handler = Handler()
if settings.client.data.components:
    handler.load(settings.client.data.components)


async def await_input():
    while True:
        try:
            message: str = input()
            await handler.process(message)
        except Exception as exception:
            print(exception)


try:
    loop.run_until_complete(await_input())
except KeyboardInterrupt:
    pass
