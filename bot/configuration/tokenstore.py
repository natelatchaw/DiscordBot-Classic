from configparser import DuplicateSectionError
from .configuration import Configuration

class TokenStore(Configuration):
    def __init__(self):
        super().__init__()
        self._sectionName = 'TOKENS'
        try:
            self.add_section(self.sectionName)
        except (ValueError, DuplicateSectionError):
            print(f'Skipping {self.sectionName} section creation during keypair add: section already exists.')
        finally:
            print(f'Initialized token store.')

    @property
    def sectionName(self):
        return self._sectionName
    @sectionName.setter
    def set_sectionName(self, name):
        # set to capitalized variant of provided name
        self._sectionName = name.upper()

    def add_token(self, tag, token):
        # if the config is missing the token section
        if not self._config.has_section(self.sectionName):
            # add the token section to the config
            self._config.add_section(self.sectionName)
        # add the tag/token pair to the token section
        self.set_key_value(self.sectionName, tag, token)
        # write changes
        self.write()

    def get_token(self, tag):
        # if the config is missing the token section
        if not self._config.has_section(self.sectionName):
            # add the token section to the config
            self.add_section(self.sectionName)
        try:
            # get the token from the config file
            token = self.get_key_value(self.sectionName, tag)
            if token == '':
                print("TOKEN IS EMPTY")
                raise TypeError(f'Token entry for tag {tag} was empty.')
            return token
        except ValueError as valueError:
            raise valueError
        except TypeError as typeError:
            raise typeError
