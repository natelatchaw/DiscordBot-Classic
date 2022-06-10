from logging import Logger
import logging
from typing import Optional
from router.configuration import Section


log: Logger = logging.getLogger(__name__)


class LimiterSettings(Section):

    @property
    def rate(self) -> float:
        key: str = "rate"
        value: Optional[str] = None
        try:
            value = self[key]
        except KeyError:
            self[key] = ""
            value = None

        if value and isinstance(value, str):
            return float(value)
        else:
            self[key] = ""
            raise ValueError(
                f"No {key} provided for {self._reference.name}:{self._name}:{key}"
            )

    @rate.setter
    def rate(self, value: float) -> None:
        key: str = "rate"
        self[key] = str(value)


    @property
    def count(self) -> Optional[int]:
        key: str = "count"
        value: Optional[str] = None
        try:
            value = self[key]
        except KeyError:
            self[key] = ""
            value = None

        if value and isinstance(value, str):
            return int(value)
        else:
            self[key] = ""
            raise ValueError(
                f"No {key} provided for {self._reference.name}:{self._name}:{key}"
            )

    @count.setter
    def count(self, value: int) -> None:
        key: str = "count"
        self[key] = str(value)