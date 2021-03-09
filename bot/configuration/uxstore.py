import pathlib
from configparser import DuplicateSectionError
from .configuration import Configuration

class UXStore(Configuration):
    def __init__(self):
        super().__init__()
        # define section name
        self._sectionName = 'UX'
        # try to initialize section in config file
        try:
            # add a section to the config file
            self.add_section(self.sectionName)
        # if the section already exists
        except (ValueError, DuplicateSectionError):
            # notify abort of section creation
            ##print(f'Skipping {self.sectionName} section creation during keypair add: section already exists.')
            pass
        finally:
            print(f'Initialized {self._sectionName} configuration store.')

    @property
    def sectionName(self):
        return self._sectionName
    @sectionName.setter
    def sectionName(self, name):
        # set to capitalized variant of provided name
        self._sectionName = name.upper()

    @property
    def prefix(self):
        entry_name = 'prefix'
        # if the config is missing the UX section
        if not self._config.has_section(self.sectionName):
            # add the UX section to the config
            self.add_section(self.sectionName)
        # try to get the entry from the config file
        try:
            prefix = self.get_key_value(self.sectionName, entry_name)
            if prefix == '':
                raise ValueError(f'The configuration entry for {entry_name} was blank.')
            return prefix
        except ValueError as valueError:
            print(f'{valueError}\nA blank {entry_name} entry has been created in the {self.sectionName} section.')
            self.set_key_value(self.sectionName, entry_name, '')
            raise
    @prefix.setter
    def prefix(self, prefix):
        entry_name = 'prefix'
        # if the entry is not a one character string
        if not (isinstance(prefix, str) and prefix.len == 1):
            raise TypeError('Prefix must be a single character string.')
        # add the UX settings pair to the UX section
        self.set_key_value(self.sectionName, entry_name, prefix)

    @property
    def owner(self):
        entry_name = 'owner'
        # if the config is missing the UX section
        if not self._config.has_section(self.sectionName):
            # add the UX section to the config
            self.add_section(self.sectionName)
        # try to get the entry from the config file
        try:
            owner = self.get_key_value(self.sectionName, entry_name)
        except ValueError as valueError:
            print(f'{valueError}\nA blank configuration entry has been created in the {self.sectionName} section for {entry_name}.')
            self.set_key_value(self.sectionName, entry_name, '')
            raise
        if owner == '':
            raise ValueError(f'The configuration entry for {entry_name} was blank.')
    @owner.setter
    def owner(self, owner): 
        entry_name = 'owner'
        # if the entry is not a string or integer
        if not isinstance(owner, str) and not isinstance(owner, int):
            raise TypeError(f'{entry_name} configuration entry must be a numeric string or an integer.')
        # try to parse the entry to an integer
        try:
            owner = int(owner)
        # if entry cannot be parsed to an integer
        except NameError:
            raise TypeError(f'Configuration entry for {entry_name} cannot be parsed to an integer.')
        # add the UX settings pair to the UX section
        self.set_key_value(self.sectionName, entry_name, owner)

    @property
    def modules(self):
        entry_name = 'modules'
        # if the config is missing the UX section
        if not self._config.has_section(self.sectionName):
            # add the UX section to the config
            self.add_section(self.sectionName)
        try:
            # get the folder name from the config file
            modules = self.get_key_value(self.sectionName, entry_name)
            # if the modules key is empty
            if modules == '':
                raise TypeError(f'Entry for {entry_name} was empty.')
            # get a Path instance from the provided string path
            path = pathlib.Path(modules)
            # if the path doesn't exist
            if not path.exists():
                # create the directory if it doesn't exist
                path.mkdir(parents=True, exist_ok=True)
            return modules
        except (ValueError, TypeError):
            raise
    @modules.setter
    def modules(self, modules):
        entry_name = 'modules'
        # get a Path instance from the provided string path
        path = pathlib.Path(modules)
        # if the path doesn't exist
        if not path.exists():
            # create the directory if it doesn't exist
            path.mkdir(parents=True, exist_ok=True)
        # add the modules path to the UX section
        self.set_key_value(self.sectionName, entry_name, modules)
