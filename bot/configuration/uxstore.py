import pathlib
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
        except (ValueError, TypeError) as error:
            print(error)
    @prefix.setter
    def prefix(self, prefix): 
        # make sure the prefix is a string of length 1
        if not isinstance(prefix, str) and prefix.len != 1:
            raise TypeError('Prefix must be a single character string.')
        # add the UX settings pair to the UX section
        self.set_key_value(self.sectionName, 'prefix', prefix)

    @property
    def modules(self):
        # if the config is missing the UX section
        if not self._config.has_section(self.sectionName):
            # add the UX section to the config
            self.add_section(self.sectionName)
        try:
            # get the folder name from the config file
            modules = self.get_key_value(self.sectionName, 'modules')
            # if the modules key is empty
            if modules == '':
                raise TypeError(f'Entry for modules was empty.')
            # get a Path instance from the provided string path
            path = pathlib.Path(modules)
            # if the path doesn't exist
            if not path.exists():
                # create the directory if it doesn't exist
                path.mkdir(parents=true, exist_ok=true)
            return modules
        except (ValueError, TypeError) as error:
            print(error)
    @modules.setter
    def modules(self, modules):
        # get a Path instance from the provided string path
        path = pathlib.Path(modules)
        # if the path doesn't exist
        if not path.exists():
            # create the directory if it doesn't exist
            path.mkdir(parents=true, exist_ok=true)
        # add the modules path to the UX section
        self.set_key_value(self.sectionName, 'modules', modules)