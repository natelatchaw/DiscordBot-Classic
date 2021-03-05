from datetime import datetime, timezone

class Snowflake():

    @classmethod
    def from_timestamp(cls, timestamp):
        if not isinstance(timestamp, datetime):
            raise ValueError("Invalid timestamp provided.")

        # if timestamp has no timezone info
        if timestamp.tzinfo is None:
            # assume UTC timezone
            timestamp = timestamp.replace(tzinfo=timezone.utc)
            print("Assuming UTC; timezone info was not provided.")

        # if timestamp is not UTC
        if timestamp.tzinfo != timezone.utc:
            # convert to UTC
            timestamp = timestamp - timestamp.utcoffset()
        # get timestamp in milliseconds
        timestamp_ms = timestamp.timestamp() * 1000
        # get discord epoch
        discord_epoch = 1420070400000
        # get snowflake
        snowflake = (timestamp_ms - discord_epoch) * 4194304
        return snowflake
        