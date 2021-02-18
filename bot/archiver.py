import discord
import sqlite3
import os

class Archiver():

    def __init__(self, channel):
        if isinstance(channel, discord.TextChannel):
            self._channel = channel
        else:
            raise TypeError('Provided channel is not a TextChannel.')

        # get the path of the data folder
        parent = os.path.abspath('data/')
        # if the data folder doesn't exist
        if not os.path.exists(parent):
            # create the data folder
            os.mkdir(parent)
        # append the database filename to the data folder path
        self._path = os.path.join(parent, f'{self._channel.guild.id}.db')
        # connect to the database
        self._connection = sqlite3.connect(self._path)
        # create the database cursor
        self._cursor = self._connection.cursor()

    async def create(self):
        create_statement = f'''
            CREATE TABLE IF NOT EXISTS CHANNEL{self._channel.id} (
                MESSAGE_ID INTEGER UNIQUE PRIMARY KEY,
                CONTENT TEXT,
                AUTHOR_ID INTEGER
            )
        '''
        try:
            self._cursor.execute(create_statement)
        except Exception as exception:
            print(exception)

    async def fetch(self, limit=None):
        
        oldest_message_id = await self.get_oldest() or None
        try:
            oldest_message_snowflake = discord.utils.snowflake_time(oldest_message_id)
        except TypeError:
            oldest_message_snowflake = None

        newest_message_id = await self.get_newest() or None
        try:
            newest_message_snowflake = discord.utils.snowflake_time(newest_message_id)
        except TypeError:
            newest_message_snowflake = None

        async for message in self._channel.history(limit=limit, before=oldest_message_snowflake):
            await self.insert(message)
        
        async for message in self._channel.history(limit=limit, after=newest_message_snowflake):
            await self.insert(message)
            

    async def insert(self, message):
        insert_statement = f'''
            INSERT INTO CHANNEL{self._channel.id} VALUES(
                ?,
                ?,
                ?
            )
        '''
        values = (
            message.id,
            message.content,
            message.author.id
        )
        try:
            self._cursor.execute(insert_statement, values)
            print(f'Message {message.id}: inserted')
            # save changes
            self._connection.commit()
        except sqlite3.IntegrityError as integrityError:
            print(f'Message {message.id}: {integrityError.args}')


    async def get_oldest(self):
        select_statement = f'''
            SELECT MESSAGE_ID FROM CHANNEL{self._channel.id}
            ORDER BY MESSAGE_ID ASC
            LIMIT 1
        '''
        self._cursor.execute(select_statement)
        # fetch the first (and only) row
        oldest_entry = self._cursor.fetchone()
        try:
            # parse the retrieved message id to an integer
            oldest_message_id = int(oldest_entry[0])
        except:
            oldest_message_id = None
        # return the oldest message id
        return oldest_message_id

    async def get_newest(self):
        select_statement = f'''
            SELECT MESSAGE_ID FROM CHANNEL{self._channel.id}
            ORDER BY MESSAGE_ID DESC
            LIMIT 1
        '''
        self._cursor.execute(select_statement)
        # fetch the first (and only) row
        newest_entry = self._cursor.fetchone()
        try:
            # parse the retrieved message id to an integer
            newest_message_id = int(newest_entry[0])
        except:
            newest_message_id = None
        # return the newest message id
        return newest_message_id

    async def get_count(self):
        select_statement = f'''
            SELECT * FROM CHANNEL{self._channel.id}
        '''
        self._cursor.execute(select_statement)
        count = len(self._cursor.fetchall())
        return count

    def close(self):
        self._connection.close()