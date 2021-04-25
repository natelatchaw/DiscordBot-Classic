from configparser import DuplicateSectionError
from .configuration import Configuration

class TokenStore(Configuration):
    def __init__(self):
        super().__init__()
        # define section name
        self._section = 'TOKENS'
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
    def mode(self):
        default_section = 'DEFAULT'
        entry_name = 'token'
        # if the config is missing the TOKEN section
        if not self._config.has_section(default_section):
            # add the TOKEN section to the config
            self.add_section(default_section)
        try:
            # get the mode value from the config file
            mode = self.get_key_value(default_section, entry_name)
            if mode == '':
                raise TypeError(f'Entry for token mode was empty.')
            return mode
        except (ValueError, TypeError) as error:
            print('Tried to get entry for token mode but the entry either did not exist or was empty.')
            raise error
    @mode.setter
    def mode(self, mode):
        default_section = 'DEFAULT'
        key = 'token'
        # add the token mode settings pair to the TOKEN section
        self.set_key_value(default_section, key, mode)

    def add_token(self, tag, token):
        # if the config is missing the token section
        if not self._config.has_section(self.section):
            # add the token section to the config
            self.add_section(self.section)
            # set the default mode to the token provided
            self.mode = tag
        # add the tag/token pair to the token section
        self.set_key_value(self.section, tag, token)

    def get_token(self, tag):
        # if the config is missing the token section
        if not self._config.has_section(self.section):
            # add the token section to the config
            self.add_section(self.section)
        try:
            # if the provided tag is None
            if tag is None:
                raise TypeError(f'Tag to retreive token entry for was type {type(tag)}.')
            # get the token from the config file
            token = self.get_key_value(self.section, tag)
            if token == '':
                raise TypeError(f'Token entry for tag {tag} was empty.')
            return token
        except (ValueError, TypeError) as error:
            raise error