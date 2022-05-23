from multiprocessing.sharedctypes import Value
from router.configuration import Section


class TokenSettings(Section):

    @property
    def active(self) -> str | None:
        defaults = self._parser.defaults()
        key: str = 'token'
        try:
            value: str | None = defaults[key]
        except KeyError:
            defaults[key] = ''
            value: str | None = None

        if value and isinstance(value, str):
            return value
        else:
            defaults[key] = ''
            self.__write__()
            raise ValueError(f'No label provided for {self._reference.name}:{self._name}:{key}')
    @active.setter
    def active(self, value: str) -> None:
        key: str = 'token'
        defaults = self._parser.defaults()
        defaults[key] = value


    @property
    def current(self) -> str | None:
        key: str | None = self.active
        try:
            value: str | None = self[key]
        except KeyError:
            self[key] = ''
            value: str | None = None

        if value and isinstance(value, str):
            return value
        else:
            self[key] = ''
            raise ValueError(f'No token provided for {self._reference.name}:{self._name}:{key}')

    
