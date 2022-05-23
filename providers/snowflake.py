from datetime import datetime, timezone

class Snowflake():

    @classmethod
    def from_timestamp(cls, timestamp: datetime) -> float:
        # validate timestamp type
        if not isinstance(timestamp, datetime): raise ValueError("Invalid timestamp provided.")

        # if timestamp has no timezone info
        if timestamp.tzinfo is None:
            # assume UTC timezone
            timestamp: datetime = timestamp.replace(tzinfo=timezone.utc)
            print(f'Assuming {timezone.utc}; timezone info was not provided.')

        # if timestamp is not UTC
        if timestamp.tzinfo != timezone.utc:
            # convert to UTC
            timestamp: datetime = timestamp - timestamp.utcoffset()

        # get timestamp in milliseconds
        timestamp_ms: float = timestamp.timestamp() * 1000
        # get discord epoch
        discord_epoch: float = 1420070400000
        # calculate snowflake
        snowflake: float = (timestamp_ms - discord_epoch) * 4194304
        
        # return 
        return snowflake
        