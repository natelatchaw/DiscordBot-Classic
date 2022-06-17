from sqlite3 import Row
from typing import Any, Dict, Tuple, Type

from database.column import ColumnBuilder
from database.storable import Storable, TStorable
from database.table import Table, TableBuilder
from discord import AudioSource


class Submission(Storable):

    def __init__(self, id: int, user_id: int, prompt: str, response: str, token_count: int) -> None:
        self._id: int = id
        self._user_id: int = user_id
        self._prompt: str = prompt
        self._response: str = response
        self._token_count: int = token_count

    @property
    def id(self) -> int:
        return self._id

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def prompt(self) -> str:
        return self._prompt

    @property
    def response(self) -> str:
        return self._response
    
    @property
    def token_count(self) -> str:
        return self._token_count

    def __table__(self) -> Table:
        # create a table builder
        t_builder: TableBuilder = TableBuilder()
        # set the table's name
        t_builder.setName('Submissions')

        # create a column builder
        c_builder: ColumnBuilder = ColumnBuilder()
        # create id column
        t_builder.addColumn(c_builder.setName('ID').setType('INTEGER').isPrimary().isUnique().column())
        # create user ID column
        t_builder.addColumn(c_builder.setName('UserID').setType('INTEGER').column())
        # create prompt column
        t_builder.addColumn(c_builder.setName('Prompt').setType('TEXT').column())
        # create response column
        t_builder.addColumn(c_builder.setName('Response').setType('TEXT').column())
        # create token count column
        t_builder.addColumn(c_builder.setName('TokenCount').setType('INTEGER').column())
        
        # build the table
        table: Table = t_builder.table()
        # return the table
        return table

    def __values__(self) -> Tuple[Any, ...]:
        # create a tuple with the corresponding values
        value: Tuple[Any, ...] = (self.id, self.user_id, self.prompt, self.response, self.token_count)
        # return the tuple
        return value

    @classmethod
    def __from_dict__(cls, dict: Dict[str, Any], snowflake: int, user_id: int):
        raise NotImplementedError()
        id: int = snowflake
        if not isinstance(id, int): raise TypeError('snowflake')
        user_id: int = user_id
        if not isinstance(user_id, int): raise TypeError('user_id')
        video_id: str = dict['id']
        if not isinstance(video_id, str): raise KeyError('id')        
        title: str = dict['title']
        if not isinstance(title, str): raise KeyError('title')        
        channel: str = dict['channel']
        if not isinstance(channel, str): raise KeyError('channel')        
        thumbnail: str = dict['thumbnail']
        if not isinstance(channel, str): raise KeyError('thumbnail')
        url: str = dict['url']
        if not isinstance(url, str): raise KeyError('url')        
        return Metadata(id, user_id, video_id, title, channel, thumbnail, url)
        
    @classmethod
    def __from_row__(cls: Type[TStorable], row: Row) -> TStorable:
        # Get ID value from the row
        id: int = row['ID']
        # Get UserID value from the row
        user_id: int = row['UserID']
        # Get VideoID value from the row
        video_id: str = row['VideoID']
        # Get URL value from the row
        url: str = row['URL']
        # Get Title value from the row
        title: str = row['Title']
        # Get Channel value from the row
        channel: str = row['Channel']
        # Get thumbnail value from the row
        thumbnail: str = row['Thumbnail']
        # return the Metadata
        return Submission(id, user_id, video_id, url, title, channel, thumbnail)