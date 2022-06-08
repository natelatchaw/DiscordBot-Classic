from datetime import datetime
import discord
from context import Context
from providers.channelArchive import ChannelArchive
from providers.guildArchive import GuildArchive

from settings import Settings

class Utility():
    """
    Provides Discord-based access to bot configuration options.
    """
    
    def __init__(self, *args, **kwargs):
        pass

    async def enable_verbose(self, context: Context):
        """
        Enables the verbose configuration flag.
        """

        context.settings.ux.verbose = True
        await context.message.reply(f"Verbose mode {'enabled' if context.settings.ux.verbose else 'disabled'}")

    async def disable_verbose(self, context: Context):
        """
        Disables the verbose configuration flag.
        """

        context.settings.ux.verbose = False
        await context.message.reply(f"Verbose mode {'enabled' if context.settings.ux.verbose else 'disabled'}")


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
        dm_channel: discord.DMChannel = await _message.author.create_dm()
        channel = _message.channel
        embed = discord.Embed()
        embed.title = f'Requested Channel IDs'
        embed.add_field(name=channel.name, value=channel.id, inline=False)
        embed.timestamp = _message.created_at
        await dm_channel.send(embed=embed)
        await _message.delete()

    async def get_channel_ids(self, *, _message: discord.Message):
        """
        DMs all IDs of channels of the guild this command is invoked in to the user that invoked the command.
        """
        dm_channel: discord.DMChannel = await _message.author.create_dm()
        embed = discord.Embed()
        embed.title = f'Requested Channel IDs'
        for channel in _message.guild.channels:
            embed.add_field(name=channel.name, value=channel.id, inline=False)
        embed.timestamp = _message.created_at
        await dm_channel.send(embed=embed)
        await _message.delete()

    async def age(self, context: Context):
        """
        Display's the creation date of the message author's account.
        """
        user: discord.User = context.message.author
        timestamp: datetime = discord.utils.snowflake_time(user.id)
        channel: discord.abc.Messageable = context.message.channel
        embed = discord.Embed()
        embed.title = f'Discord user since {timestamp.year}'
        embed.set_author(name=user.name, icon_url=user.avatar_url)
        embed.timestamp = timestamp
        await channel.send(embed=embed)

    async def count(self, context: Context):
        """
        """

        guildArchive: GuildArchive = context.archive._archives[context.message.guild.id]
        channelArchive: ChannelArchive = guildArchive._archives[context.message.channel.id]
        length = len(channelArchive)
        await context.message.reply(length)