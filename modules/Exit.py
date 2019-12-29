import os
import discord

class Exit():
    def __init__(self, args):
        self.name = 'Exit'
        self.description = 'Shuts down the bot'
        self.syntax = ['exit']

    async def run(self):
        print('[%16s]Shutting down...' % os.path.basename(__file__))
        return 'cy@'
