from re import match
import re
from typing import Any, Dict, List, Optional
from router import Handler, HandlerError
from discord import Message

from context import Context

class CommandHandler(Handler):

    async def process(self, prefix: str, message: Message, *, context: Context):
        # create args list from context instance
        args: List[Any] = [context]
        # get command from message
        command_match: match = re.match(rf'^{prefix}[\w]+', message.content)
        # if the prefixed command could not be found at the beginning of the message
        if not command_match: raise MissingPrefixError()
        # remove prefix from message content
        command_message: str = re.sub(rf'^{prefix}', '', message.content)
        # call superclass to finish processing the message
        await super().process(command_message, args=args)

class MissingPrefixError(HandlerError):
    def __init__(self, exception: Optional[Exception] = None):
        message: str = f'Message did not begin with a prefix.'
        super().__init__(message, exception)