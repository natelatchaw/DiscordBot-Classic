from sqlite3 import Row
from typing import Any, Dict, Tuple, Type

from database.column import ColumnBuilder
from database.storable import Storable, TStorable
from database.table import Table, TableBuilder
from discord import AudioSource


class Metadata(Storable):

    def __init__(self, id: int, user_id: int, video_id: str, title: str, channel: str, thumbnail: str, url: str) -> None:
        self._id: int = id
        self._user_id: int = user_id
        self._video_id: str = video_id
        self._title: str = title
        self._channel: str = channel
        self._thumbnail: str = thumbnail
        self._url: str = url

    def __str__(self) -> str:
        return f'[{self._video_id}] {self._title} ({self._url})'

    @property
    def id(self) -> int:
        return self._id

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def video_id(self) -> str:
        return self._video_id

    @property
    def title(self) -> str:
        return self._title
    
    @property
    def channel(self) -> str:
        return self._channel
    
    @property
    def thumbnail(self) -> str:
        return self._thumbnail

    @property
    def url(self) -> str:
        return self._url

    @classmethod
    def __table__(self) -> Table:
        # create a table builder
        t_builder: TableBuilder = TableBuilder()
        # set the table's name
        t_builder.setName('Metadata')

        # create a column builder
        c_builder: ColumnBuilder = ColumnBuilder()
        # create timestamp column
        t_builder.addColumn(c_builder.setName('ID').setType('INTEGER').isPrimary().isUnique().column())
        # create user ID column
        t_builder.addColumn(c_builder.setName('UserID').setType('INTEGER').column())
        # create video ID column
        t_builder.addColumn(c_builder.setName('VideoID').setType('TEXT').column())
        # create title column
        t_builder.addColumn(c_builder.setName('Title').setType('TEXT').column())
        # create channel column
        t_builder.addColumn(c_builder.setName('Channel').setType('TEXT').column())
        # create channel column
        t_builder.addColumn(c_builder.setName('Thumbnail').setType('TEXT').column())
        # create url column
        t_builder.addColumn(c_builder.setName('URL').setType('TEXT').column())
        
        # build the table
        table: Table = t_builder.table()
        # return the table
        return table

    def __values__(self) -> Tuple[Any, ...]:
        # create a tuple with the corresponding values
        value: Tuple[Any, ...] = (self.id, self.user_id, self.video_id, self.title, self.channel, self.thumbnail, self.url)
        # return the tuple
        return value

    @classmethod
    def __from_dict__(cls, dict: Dict[str, Any], snowflake: int, user_id: int):
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
        return Metadata(id, user_id, video_id, url, title, channel, thumbnail)


class AudioRequest():
    """
    A request object for the bot to play.
    """

    def __init__(self, source: AudioSource, metadata: Metadata):
        self._metadata: Metadata = metadata
        self._source: AudioSource = source
    
    @property
    def metadata(self) -> Metadata:
        return self._metadata

    @property
    def source(self) -> AudioSource:
        return self._source

