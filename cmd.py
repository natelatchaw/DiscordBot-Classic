import asyncio

from bot.core import Core
from bot.handler import Handler

loop = asyncio.get_event_loop()

core = Core()

handler = Handler(core)

async def await_input():
    while True:
        message: str = input()
        try:
            await handler.process(message)
        except Exception as exception:
            print(exception)

loop.run_until_complete(await_input())
