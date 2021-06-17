from typing import Any, Dict
import discord
from router.error.configuration import ConfigurationError
from router.logger import Logger
from router.settings import Settings

class MessageLogger(Logger):

    def __init__(self, settings: Settings, guild: discord.Guild):
        super().__init__(settings)
        self.guild = guild

    async def print(self, message: discord.Message):
        author: str = message.author.display_name[:17] + '...' if len(message.author.display_name) > 20 else message.author.display_name
        channel: str = message.channel.name[:17] + '...' if len(message.channel.name) > 20 else message.channel.name
        content: str = message.clean_content[:77] + '...' if len(message.clean_content) > 80 else message.clean_content
        print(f'{author:<20} #{channel:<20} {content:<80}')