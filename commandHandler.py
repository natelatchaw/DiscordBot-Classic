import logging
import re
import textwrap
import traceback
from datetime import datetime, timezone
from logging import Logger
from re import Match
from typing import Any, List, Literal, Optional

from discord import Embed, Message
from router import Handler, HandlerError

from context import Context
from rateLimiter import RateLimiter

log: Logger = logging.getLogger(__name__)

MAX_MESSAGE_SIZE: Literal[2000] = 2000
"""
The maximum amount of characters
permitted in a Discord message
"""


class CommandHandler(Handler):

    def __init__(self, parameter_prefix: str = '-'):
        self._limiter: Optional[RateLimiter] = None
        super().__init__(parameter_prefix)

    def __build_error_message__(self, error: Exception) -> Embed:
        embed: Embed = Embed()

        embed.title = f'{type(error).__name__}'
        embed.description = f'An error occurred during command execution.'
        embed.add_field(name='Details', value=str(error), inline=False)
        embed.timestamp = datetime.now(tz=timezone.utc)
        
        return embed


    def addLimiter(self, limiter: RateLimiter) -> None:
        self._limiter = limiter

    async def handle(self, prefix: str, message: Message, *, context: Context):

        try:
            # create args list from context instance
            args: List[Any] = [context]
            # get command from message
            command_match: Optional[Match[Any]] = re.match(rf"^{prefix}[\w]+", message.content)
            # if the prefixed command could not be found at the beginning of the message
            if not command_match: raise MissingPrefixError()
            # remove prefix from message content
            command_message: str = re.sub(rf"^{prefix}", "", message.content)
        except MissingPrefixError:
            raise
        except Exception as error:
            raise MessageParseError(error)
            
        try:
            # ratelimit check the message if available
            if self._limiter: self._limiter.check(message)
            # trigger typing indicator
            await context.message.channel.trigger_typing()
            # call super to finish processing the message
            await super().process(command_message, args=args)
        except Exception as error:
            log.error(error)
            log.error(''.join(traceback.format_tb(error.__traceback__)))

            embed: Embed = self.__build_error_message__(error)
            embed.set_author(name=context.client.user.name, icon_url=str(context.client.user.avatar_url))
            await message.reply(embed=embed)

            if context.message.guild and context.settings.for_guild(context.message.guild).ux.verbose:
                await self.__print_traceback__(context, error)

    async def __print_traceback__(self, context: Context, error: Exception) -> None:
        """
        Assembles and splits the traceback to message lengths
        compatible with a standard Discord message.
        """
        # assemble the trace
        trace: str = ''.join(traceback.format_tb(error.__traceback__))
        # define the block tag for code block messages
        block_tag: str = '```'
        # calculate the max characters that can be inserted into each message's code block
        max_characters: int = MAX_MESSAGE_SIZE - (2 * len(block_tag))
        # break the response into string segments with length equivalent to the maximum character limit
        segments: List[str] = textwrap.wrap(trace, max_characters, break_long_words=False, replace_whitespace=False)
        # set the initial message reference to the original message
        message: Message = context.message
        # for each segment# for each segment
        for segment in segments:
            # send the message and set the message reference to the sent message
            message = await message.reply(f'{block_tag}\n{segment}\n{block_tag}')




class MissingPrefixError(HandlerError):
    def __init__(self, exception: Optional[Exception] = None):
        message: str = f'Message did not begin with a prefix.'
        super().__init__(message, exception)

class MessageParseError(HandlerError):
    def __init__(self, exception: Optional[Exception] = None):
        message: str = f'An error occurred while parsing the message: {str(exception) if exception else "No info provided"}'
        super().__init__(message, exception)
