import logging
import re
from logging import Logger
from re import Match
import traceback
from typing import Any, List, Optional

from discord import Message
from router import Handler, HandlerError

from context import Context

log: Logger = logging.getLogger(__name__)


class CommandHandler(Handler):

    async def handle(self, prefix: str, message: Message, *, context: Context):
        # create args list from context instance
        args: List[Any] = [context]
        # get command from message
        command_match: Optional[Match[Any]] = re.match(
            rf"^{prefix}[\w]+", message.content
        )
        # if the prefixed command could not be found at the beginning of the message
        if not command_match: raise MissingPrefixError()
        # remove prefix from message content
        command_message: str = re.sub(rf"^{prefix}", "", message.content)

        try:
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
