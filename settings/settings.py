from pathlib import Path
from typing import cast

from router.configuration import Configuration
from settings.limiting import LimiterSettings

from settings.token import TokenSettings
from settings.ux import UXSettings


class Settings(Configuration):
    def __init__(self, reference: Path = Path('./config.ini')):
        super().__init__(reference)
        self['UX'] = UXSettings('UX', self._parser, self._reference)
        self['TOKENS'] = TokenSettings('TOKENS', self._parser, self._reference)
        self['LIMITING'] = LimiterSettings('LIMITING', self._parser, self._reference)

    @property
    def ux(self) -> UXSettings:
        return cast(UXSettings, self['UX'])

    @property
    def token(self) -> TokenSettings:
        return cast(TokenSettings, self['TOKENS'])

    @property
    def limiting(self) -> LimiterSettings:
        return cast(LimiterSettings, self['LIMITING'])
