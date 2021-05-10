import discord
from bot.core import Core

class Logger():
    
    def __init__(self, core: Core, guild: discord.Guild):
        self.core = core
        self.guild = guild

    async def print(self, *args):
        message = '\n'.join(args)
        try:
            # get the logging channel id from the config
            channel_id: int = self.core.logging_channel
        except (TypeError, ValueError):
            return
        # get the channel object from the channel id
        logging_channel = self.guild.get_channel(channel_id)
        if not isinstance(logging_channel, discord.TextChannel):
            return
        await logging_channel.send(f'{message}')

