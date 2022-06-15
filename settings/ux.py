import logging
from logging import Logger
from pathlib import Path
from typing import Optional

from settings.section import SettingsSection

log: Logger = logging.getLogger(__name__)


class UXSettings(SettingsSection):
    @property
    def components(self) -> Optional[Path]:
        key: str = "components"
        return self.get_path(key)
    @components.setter
    def components(self, reference: Path) -> None:
        key: str = "components"
        self[key] = str(reference)

    @property
    def prefix(self) -> Optional[str]:
        key: str = "prefix"
        return self.get_string(key)
    @prefix.setter
    def prefix(self, value: str) -> None:
        key: str = "prefix"
        self[key] = value


    @property
    def owner(self) -> Optional[int]:
        key: str = "owner"
        return self.get_integer(key)
    @owner.setter
    def owner(self, value: int) -> None:
        key: str = "owner"
        self[key] = str(value)


    @property
    def verbose(self) -> bool:
        key: str = "verbose"
        value: Optional[bool] = self.get_boolean(key)
        return value if value else False
    @verbose.setter
    def verbose(self, value: bool) -> None:
        key: str = "verbose"
        self[key] = str(value)
