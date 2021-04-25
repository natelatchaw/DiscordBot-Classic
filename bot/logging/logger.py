import discord
from ..core import Core

class Logger():

    @staticmethod
    async def print(core: Core, guild: discord.Guild, message: str):
        try:
            # get the logging channel id from the config
            channel_id: int = core.logging_channel
        except (TypeError, ValueError) as error:
            return
        # get the channel object from the channel id
        logging_channel = guild.get_channel(channel_id)
        if not isinstance(logging_channel, discord.TextChannel):
            return
        await logging_channel.send(f'{message}')

