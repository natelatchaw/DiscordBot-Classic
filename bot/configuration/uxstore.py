from configparser import DuplicateSectionError
from .configuration import Configuration

class UXStore(Configuration):
    def __init__(self):
        super().__init__()
        self._sectionName = 'UX'
        try:
            self.add_section(self.sectionName)
        except (ValueError, DuplicateSectionError):
            print(f'Skipping {self.sectionName} section creation during keypair add: section already exists.')
        finally:
            print(f'Initialized UX settings store.')

    @property
    def sectionName(self):
        return self._sectionName
    @sectionName.setter
    def sectionName(self, name):
        # set to capitalized variant of provided name
        self._sectionName = name.upper()

    @property
    def prefix(self):
        # if the config is missing the UX section
        if not self._config.has_section(self.sectionName):
            # add the UX section to the config
            self.add_section(self.sectionName)
        try:
            # get the prefix value from the config file
            token = self.get_key_value(self.sectionName, 'prefix')
            if token == '':
                raise TypeError(f'Entry for prefix was empty.')
            return token
        except ValueError as valueError:
            print(valueError)
        except TypeError as typeError:
            print(typeError)
    @prefix.setter
    def prefix(self, prefix): 
        # make sure the prefix is a string of length 1
        if not isinstance(prefix, str) and prefix.len != 1:
            raise TypeError('Prefix must be a single character string.')
        # add the UX settings pair to the UX section
        self.set_key_value(self.sectionName, 'prefix', prefix)