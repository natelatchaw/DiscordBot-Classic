import logging
import sys
from logging import FileHandler, Formatter, Logger, StreamHandler

import discord
import router

import core
import providers.archiver
from core import Core

root: Logger = logging.getLogger()

formatter: Formatter = Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s')
# formatter: Formatter = Formatter('[%(asctime)s] [%(pathname)s:%(lineno)d] [%(name)s] [%(levelname)s] %(message)s')
# formatter: Formatter = Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')

stdoutHandler: StreamHandler = StreamHandler(sys.stdout)
stdoutHandler.setFormatter(formatter)
stdoutHandler.setLevel(logging.INFO)
root.addHandler(stdoutHandler)

fileHandler: FileHandler = FileHandler("./.log", encoding="utf-8")
fileHandler.setFormatter(formatter)
fileHandler.setLevel(logging.DEBUG)
root.addHandler(fileHandler)

logging.addLevelName(logging.DEBUG, "DBG")
logging.addLevelName(logging.INFO, "INF")
logging.addLevelName(logging.WARN, "WRN")
logging.addLevelName(logging.ERROR, "ERR")
logging.addLevelName(logging.FATAL, "FTL")

logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger(discord.__name__).setLevel(logging.WARNING)
logging.getLogger(core.__name__).setLevel(logging.DEBUG)
logging.getLogger(providers.archiver.__name__).setLevel(logging.DEBUG)
logging.getLogger(router.__name__).setLevel(logging.INFO)
logging.getLogger(router.packaging.__name__).setLevel(logging.INFO)
logging.getLogger(router.packaging.__name__).setLevel(logging.INFO)
logging.getLogger(router.packaging.__name__).setLevel(logging.INFO)

log: Logger = logging.getLogger(__name__)

try:
    client = Core()
    client.loop.run_until_complete(client.start(client._settings.token.current))
except KeyboardInterrupt:
    client.loop.run_until_complete(client.close())
except Exception as error:
    log.error(error)
    client.loop.run_until_complete(client.close())
finally:
    client.loop.close()
    sys.exit(input('Press enter to exit...'))
