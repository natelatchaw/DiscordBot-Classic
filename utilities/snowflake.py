import logging
from datetime import datetime, timezone
from logging import Logger
from typing import Literal

log: Logger = logging.getLogger(__name__)

# define discord epoch
DISCORD_EPOCH: Literal[1420070400000] = 1420070400000


class Snowflake:

    @classmethod
    def from_timestamp(cls, timestamp: datetime) -> float:

        # validate timestamp type
        if not isinstance(timestamp, datetime):
            raise ValueError("Invalid timestamp provided.")

        # if timestamp has no timezone info
        if timestamp.tzinfo is None:
            log.info(f'Timestamp is missing timezone info; assuming {timezone.utc}')
            # replace timezone with UTC timezone
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        # if timestamp has UTC timezone
        elif timestamp.tzinfo is timezone.utc:
            log.info(f'Timestamp indicates {timestamp.tzinfo} timezone')
            # no alteration necessary
            pass

        # if timestamp has timezone info
        else:
            log.info(f'Timestamp indicates {timestamp.tzinfo} timezone; converting to {timezone.utc}')
            # convert to UTC
            timestamp = timestamp.astimezone(tz=timezone.utc)
        
        # get timestamp in milliseconds
        timestamp_ms: float = timestamp.timestamp() * 1000

        # calculate snowflake
        snowflake: int = int(timestamp_ms - DISCORD_EPOCH) << 22

        # return snowflake
        return Snowflake(snowflake)

    @property
    def timestamp(self) -> int:
        shift: int = 22
        mask: int = 0x3FFFFFFFFC00000
        offset: int = DISCORD_EPOCH
        return self.__calculate__(shift, mask, offset)

    @property
    def worker(self) -> int:
        shift: int = 17
        mask: int = 0x0000000003E0000
        offset: int = 0
        return self.__calculate__(shift, mask, offset)

    @property
    def process(self) -> int:
        shift: int = 12
        mask: int = 0x00000000001F000
        offset: int = 0
        return self.__calculate__(shift, mask, offset)

    @property
    def increment(self) -> int:
        shift: int = 12
        mask: int = 0x000000000000FFF
        offset: int = 0
        return self.__calculate__(shift, mask, offset)

    def __init__(self, value: int) -> None:
        self._value: int = value

    def __calculate__(self, shift: int, mask: int, offset: int) -> int:
        return ((self._value & mask) >> shift) + offset
