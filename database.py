
from abc import abstractmethod
from pathlib import Path
from sqlite3 import Connection, Cursor, Row
import sqlite3
from typing import Any, Callable, Dict, List, Protocol, Tuple, Type, TypeVar
from table import Table

TStorable = TypeVar('TStorable', bound='Storable')


class Storable(Protocol):
    
    @abstractmethod
    def __table__(self) -> Table:
        raise NotImplementedError()

    @abstractmethod
    def __values__(self) -> Tuple[Any, ...]:
        raise NotImplementedError()

    @abstractmethod
    def __from_row__(cls: Type[TStorable], row: Row) -> TStorable:
        raise NotImplementedError()


class Database():

    def __init__(self, reference: Path) -> None:
        # create an absolute reference to the database
        self._database: Path = reference.absolute()
        # if the database file does not exist, create it
        if not self._database.exists(): self._database.touch(exist_ok=True)

        # connect to the database
        self._connection: Connection = sqlite3.connect(self._database)
        # set the connection's row factory
        self._connection.row_factory = Row

    def create(self, type: Type[TStorable]) -> None:
        # get the table instance
        table: Table = type.__table__()
        # execute the table's create statement
        self._connection.cursor().execute(table.__create__(if_not_exists=True))
        # commit the changes
        self._connection.commit()

    def insert(self, type: Type[TStorable]) -> None:
        # get the table instance
        table: Table = type.__table__()
        # execute the table's insert statement with parameter injection
        self._connection.cursor().execute(table.__insert__(), type.__values__())
        # commit the changes
        self._connection.commit()