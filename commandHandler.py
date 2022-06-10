import logging
import re
from logging import Logger
from re import Match
from tkinter.messagebox import NO
import traceback
from typing import Any, List, Optional

from discord import Message
from router import Handler, HandlerError

from context import Context
from rateLimiter import RateLimiter

log: Logger = logging.getLogger(__name__)


class CommandHandler(Handler):

    def __init__(self, parameter_prefix: str = '-'):
        self._limiter: Optional[RateLimiter] = None
        super().__init__(parameter_prefix)

    def addLimiter(self, limiter: RateLimiter) -> None:
        self._limiter: RateLimiter = limiter

    async def handle(self, prefix: str, message: Message, *, context: Context):
        # create args list from context instance
        args: List[Any] = [context]
        # get command from message
        command_match: Optional[Match[Any]] = re.match(rf"^{prefix}[\w]+", message.content)
        # if the prefixed command could not be found at the beginning of the message
        if not command_match: raise MissingPrefixError()
        # remove prefix from message content
        command_message: str = re.sub(rf"^{prefix}", "", message.content)


        try:
            # ratelimit check the message if available
            if self._limiter: self._limiter.check(message)
            # call superclass to finish processing the message
            await super().process(command_message, args=args)
        except Exception as error:
            log.error(error)

            response: str = f'An error occurred during command execution'
            if True:
                response = response + f":```{error}```"
            if context.settings.ux.verbose:
                response = response + f"```{''.join(traceback.format_tb(error.__traceback__))}```"
            await message.reply(response)


class MissingPrefixError(HandlerError):
    def __init__(self, exception: Optional[Exception] = None):
        message: str = f"Message did not begin with a prefix."
        super().__init__(message, exception)
