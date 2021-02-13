import os
import discord

class Exit():
    def __init__(self, args):
        self.name = 'Exit'
        self.description = 'Shuts down the bot'
        self.syntax = ['exit']

    async def run(self):
        goodbye = f'{self.message.guild.default_role} actually going away now. See you boys in August. I\'ll probably write Don because he\'s the only address I can remember. See ya in a few months.'
        await self.message.channel.send(goodbye)
        await self.client.close()
        await client.change_presence(status = discord.Status.offline)
        print(f'{os.path.basename(__file__):{self.configuration.getConsoleSpacing()}}Shutting down...')
