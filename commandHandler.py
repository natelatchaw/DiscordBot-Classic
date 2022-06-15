from datetime import datetime, timezone
import logging
import re
import traceback
from logging import Logger
from re import Match
from typing import Any, List, Optional

from discord import Embed, Message
from router import Handler, HandlerError

from context import Context
from rateLimiter import RateLimiter

log: Logger = logging.getLogger(__name__)


class CommandHandler(Handler):

    def __init__(self, parameter_prefix: str = '-'):
        self._limiter: Optional[RateLimiter] = None
        super().__init__(parameter_prefix)

    def __build_error_message__(self, error: Exception, use_verbose: bool = False) -> Embed:
        embed: Embed = Embed()

        embed.title = f'{type(error).__name__}'
        embed.description = f'An error occurred during command execution.'
        embed.add_field(name='Details', value=str(error), inline=False)
        embed.timestamp = datetime.now(tz=timezone.utc)

        if use_verbose:
            trace: str = ''.join(traceback.format_tb(error.__traceback__))
            embed.add_field(name='Traceback', value=trace, inline=False)
        
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
        except Exception as error:
            raise MessageParseError(error)
            
        try:
            # ratelimit check the message if available
            if self._limiter: self._limiter.check(message)
            # call super to finish processing the message
            await super().process(command_message, args=args)
        except Exception as error:
            log.error(error)
            log.error(''.join(traceback.format_tb(error.__traceback__)))

            embed: Embed = self.__build_error_message__(error, context.settings.ux.verbose)
            embed.set_author(name=context.client.user.name, icon_url=str(context.client.user.avatar_url))
            await message.reply(embed=embed)


class MissingPrefixError(HandlerError):
    def __init__(self, exception: Optional[Exception] = None):
        message: str = f'Message did not begin with a prefix.'
        super().__init__(message, exception)

class MessageParseError(HandlerError):
    def __init__(self, exception: Optional[Exception] = None):
        message: str = f'An error occurred while parsing the message: {str(exception) if exception else "No info provided"}'
        super().__init__(message, exception)
