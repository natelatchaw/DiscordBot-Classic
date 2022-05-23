from pathlib import Path

from router.configuration import Configuration

from settings.token import TokenSettings
from settings.ux import UXSettings


class Settings(Configuration):

    def __init__(self, reference: Path = Path('./config.ini')):
        super().__init__(reference)
        self['UX'] = UXSettings('UX', self._parser, self._reference)
        self['TOKENS'] = TokenSettings("TOKENS", self._parser, self._reference)

    @property
    def ux(self) -> UXSettings:
        return self['UX']

    @property
    def token(self) -> TokenSettings:
        return self['TOKENS']