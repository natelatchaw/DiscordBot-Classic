import logging
from logging import Logger
from pathlib import Path
from typing import Optional

from router.configuration import Section

log: Logger = logging.getLogger(__name__)


class UXSettings(Section):
    @property
    def components(self) -> Path:
        key: str = "components"
        value: Optional[str] = None
        try:
            value = self[key]
        except KeyError:
            self[key] = ""

        if value and isinstance(value, str):
            return self.create_directory(key, value)
        else:
            self[key] = ""
            raise ValueError(
                f"No directory provided for {self._reference.name}:{self._name}:{key}"
            )

    @components.setter
    def components(self, reference: Path) -> None:
        key: str = "components"
        self[key] = str(reference)

    @property
    def prefix(self) -> str:
        key: str = "prefix"
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
                f"No {key} provided for {self._reference.name}:{self._name}:{key}"
            )

    @prefix.setter
    def prefix(self, prefix: str) -> None:
        key: str = "prefix"
        self[key] = prefix

    @property
    def owner(self) -> Optional[int]:
        key: str = "owner"
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

    @owner.setter
    def owner(self, owner: int) -> None:
        key: str = "owner"
        self[key] = str(owner)

    @property
    def verbose(self) -> bool:
        key: str = "verbose"
        value: Optional[str] = None
        try:
            value = self[key]
        except KeyError:
            self[key] = ""

        if value and isinstance(value, str):
            return value.lower() == str(True).lower()
        else:
            return False
    @verbose.setter
    def verbose(self, value: bool) -> None:
        key: str = "verbose"
        self[key] = str(value)

    def create_directory(self, key: str, value: str) -> Path:
        directory: Path = Path(value).resolve()
        if not directory.exists():
            log.debug("Starting %s directory creation at %s", key, directory)
            directory.mkdir(parents=True, exist_ok=True)
            return directory
        else:
            log.debug("Existing %s directory found at %s", key, directory)
            return directory
