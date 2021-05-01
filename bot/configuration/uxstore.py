import pathlib
from configparser import DuplicateSectionError
from bot.configuration.configuration import Configuration

class UXStore(Configuration):
    def __init__(self):
        super().__init__()
        # define section name
        self._section = 'UX'
        # try to initialize section in config file
        try:
            # add a section to the config file
            self.add_section(self.section)
        # if the section already exists
        except (ValueError, DuplicateSectionError):
            # notify abort of section creation
            ##print(f'Skipping {self.sectionName} section creation during keypair add: section already exists.')
            pass
        finally:
            print(f'Initialized {self._section} configuration store.')

    @property
    def section(self):
        return self._section
    @section.setter
    def section(self, name):
        # set to capitalized variant of provided name
        self._section = name.upper()

    @property
    def prefix(self):
        try:
            return self.get_character(self.section, 'prefix')
        except ValueError:
            raise
    @prefix.setter
    def prefix(self, prefix: str):
        try:
            self.set_character(self.section, 'prefix', prefix)
        except ValueError:
            raise

    @property
    def owner(self):
        try:
            return self.get_integer(self.section, 'owner')
        except ValueError:
            raise
    @owner.setter
    def owner(self, owner_id: int):
        try:
            self.set_integer(self.section, 'owner', owner_id)
        except ValueError:
            raise

    @property
    def modules(self) -> str:
        try:
            return self.get_folder(self.section, 'modules')
        except ValueError:
            raise
    @modules.setter
    def modules(self, modules: str):
        try:
            self.set_folder(self.section, 'modules', modules)
        except ValueError:
            raise
        
    @property
    def logging_channel(self) -> int:
        try:
            return self.get_integer(self.section, 'logging_channel')
        except ValueError:
            raise
    @logging_channel.setter
    def logging_channel(self, channel_id: int):
        try:
            self.set_integer(self.section, 'logging_channel', channel_id)
        except ValueError:
            raise
