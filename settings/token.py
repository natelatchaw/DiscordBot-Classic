from logging import Logger
import logging
from typing import MutableMapping, Optional
from router.configuration import Section


log: Logger = logging.getLogger(__name__)

class TokenSettings(Section):
    @property
    def active(self) -> str:
        defaults: MutableMapping[str, str] = self._parser.defaults()
        key: str = "token"
        value: Optional[str] = None
        try:
            value = defaults[key]
        except KeyError:
            defaults[key] = ""

        if value and isinstance(value, str):
            return value
        else:
            defaults[key] = ""
            self.__write__()
            raise ValueError(
                f"No label provided for {self._reference.name}:{self._name}:{key}"
            )

    @active.setter
    def active(self, value: str) -> None:
        key: str = "token"
        defaults: MutableMapping[str, str] = self._parser.defaults()
        defaults[key] = value

    @property
    def current(self) -> str:
        key: str = self.active
        value: Optional[str] = None
        try:
            value = self[key]
        except KeyError:
            self[key] = ""

        if value and isinstance(value, str):
            return value
        else:
            self[key] = ""
            raise ValueError(
                f"No token provided for {self._reference.name}:{self._name}:{key}"
            )
