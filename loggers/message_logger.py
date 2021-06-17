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
        message_content: str = message.clean_content
        content: str = message_content[:77] + '...' if len(message_content) > 80 else message_content
        print(f'{message.author.display_name:<20} {message.channel.name:<20} {content:<80}')