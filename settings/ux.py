import logging
from pathlib import Path
from router.configuration import Section


class UXSettings(Section):

    @property
    def components(self) -> Path | None:
        key: str = 'components'
        try:
            value: str | None = self[key]
        except KeyError:
            self[key] = ''
            value: str | None = None

        if value and isinstance(value, str):
            return self.create_directory(key, value)
        else:
            self[key] = ''
            raise ValueError(f'No {key} provided for {self._reference.name}:{self._name}:{key}')
    @components.setter
    def components(self, reference: Path) -> None:
        key: str = 'components'
        self[key] = str(reference)

    @property
    def prefix(self) -> str | None:
        key: str = 'prefix'
        try:
            value: str | None = self[key]
        except KeyError:
            self[key] = ''
            value: str | None = None

        if value and isinstance(value, str):
            return value
        else:
            self[key] = ''
            raise ValueError(f'No {key} provided for {self._reference.name}:{self._name}:{key}')
    @prefix.setter
    def prefix(self, prefix: str) -> None:
        key: str = 'prefix'
        self[key] = prefix

    @property
    def owner(self) -> int | None:
        key: str = 'owner'
        try:
            value: str | None = self[key]
        except KeyError:
            self[key] = ''
            value: str | None = None

        if value and isinstance(value, str):
            return int(value)
        else:
            self[key] = ''
            raise ValueError(f'No {key} provided for {self._reference.name}:{self._name}:{key}')
    @owner.setter
    def owner(self, owner: int) -> None:
        key: str = 'owner'
        self[key] = str(owner)
    
    def create_directory(self, key: str, value: str) -> Path:
        directory: Path = Path(value).resolve()
        if not directory.exists():
            logging.debug('Starting %s directory creation at %s', key, directory)
            directory.mkdir(parents=True, exist_ok=True)
            return directory
        elif directory.exists():
            logging.debug('Existing %s directory found at %s', key, directory)
            return directory

