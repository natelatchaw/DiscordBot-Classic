import discord
from router.settings import Settings

class Utility():
    """
    Provides Discord-based access to bot configuration options.
    """
    
    def __init__(self):
        pass

    async def set_log_channel(self, *, _message: discord.Message, _settings: Settings, reset: bool=False):
        """
        Specifies the channel that the command is invoked in as the channel that the bot should output log data to.

        Parameters:
            - reset: A boolean value determining whether the specified log channel should be reset to the default value: None.
        """
        if not isinstance(_message.channel, discord.TextChannel):
            await _message.channel.send(f'Channel {_message.channel.mention} cannot be used for logging.')
            return
        if reset:
            _settings.logging_channel = None
            return
        try:
            _settings.logging_channel = _message.channel.id
            await _message.channel.send(f'Channel {_message.channel.mention} set as log channel.')
        except ValueError as valueError:
            await _message.channel.send(valueError)

    async def get_channel_id(self, *, _message: discord.Message):
        """
        DMs the ID of the channel this command is invoked in to the user that invoked the command.
        """
        dm_channel: discord.DMChannel = _message.author.create_dm()
        embed = discord.Embed()
        embed.title = f'{_message.channel.mention} Channel ID'
        embed.description = _message.channel.id
        embed.timestamp = _message.created_at
        await dm_channel.send(embed=embed)