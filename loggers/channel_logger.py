import discord
from router.error.configuration import ConfigurationError
from router.logger import Logger
from router.settings import Settings

class ChannelLogger(Logger):

    def __init__(self, settings: Settings, guild: discord.Guild):
        super().__init__(settings)
        self.guild = guild

    async def print(self, *args, **kwargs):
        if not self.guild:
            return

        message = '\n'.join(args)
        try:
            # get the logging channel id from the config
            channel_id: int = self.settings.logging_channel
        except ConfigurationError:
            return
        # get the channel object from the channel id
        logging_channel = self.guild.get_channel(channel_id)
        if not isinstance(logging_channel, discord.TextChannel):
            return
        await logging_channel.send(f'{message}')
