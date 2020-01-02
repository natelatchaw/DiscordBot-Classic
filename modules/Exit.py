import os
import discord

class Exit():
    def __init__(self, args):
        self.name = 'Exit'
        self.description = 'Shuts down the bot'
        self.syntax = ['exit']

    async def run(self):
        print(f'{os.path.basename(__file__):16}Shutting down...')
        return 'cy@'
