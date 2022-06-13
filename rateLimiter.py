from datetime import datetime, timedelta, timezone
import logging
from logging import Logger
from typing import Dict, Optional, Union
from collections import deque

from discord import Message, User, Member

from settings.settings import Settings

log: Logger = logging.getLogger(__name__)

class RateLimiter():

    def __init__(self, settings: Settings) -> None:
        self._settings: Settings = settings
        self._history: Dict[int, deque] = dict()

    def check(self, message: Message) -> None:
        '''
        Checks if the message meets the rate limit policy.
        Raises an error if message fails to meet policy.
        '''

        try:
            rate: float = self._settings.limiting.rate
            count: int = self._settings.limiting.count
        except ValueError as error:
            log.warning(error)
            return

        author: Union[User, Member] = message.author
        timestamp: datetime = message.created_at

        if author.id not in self._history.keys():
            self._history[author.id] = deque(maxlen=count)

        queue: deque = self._history[author.id]
        
        log.info(f'cur: {len(queue)}')
        log.info(f'max: {queue.maxlen}')

        try:
            oldest: datetime = queue[0]
            delta: timedelta = timestamp - oldest
            if delta.total_seconds() < rate:
                raise RateLimitActiveException(delta, rate)
            # append the current message's timestamp to the deque
            queue.append(timestamp)

        except IndexError as error:
            # append the current message's timestamp to the deque
            queue.append(timestamp)


class RateLimiterError(Exception):
    """Base exception class for rate limiter related errors."""
    
    def __init__(self, message: str, exception: Optional[Exception] = None):
        self._message = message
        self._inner_exception = exception

    def __str__(self) -> str:
        return self._message


class RateLimitActiveException(RateLimiterError):
    def __init__(self, delta: timedelta, rate: float, exception: Optional[Exception] = None):
        remaining: float = rate - delta.total_seconds()
        message: str = f'Triggered rate limit: try again in {"%.2f" % remaining}s'
        super().__init__(message, exception)
