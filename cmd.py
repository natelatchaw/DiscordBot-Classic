import asyncio

from router.settings import Settings
from router.handler import Handler

loop = asyncio.get_event_loop()

settings = Settings()
handler = Handler()
handler.load(settings.modules)

async def await_input():
    while True:
        message: str = input()
        try:
            await handler.process(settings.prefix, message)
        except Exception as exception:
            print(exception)

loop.run_until_complete(await_input())
