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
        entryName = 'prefix'
        # if the config is missing the UX section
        if not self._config.has_section(self.sectionName):
            # add the UX section to the config
            self.add_section(self.sectionName)
        # try to get the entry from the config file
        try:
            prefix = self.get_key_value(self.sectionName, entryName)
        except ValueError as valueError:
            print(f'{valueError}\nA blank {entryName} entry has been created in the {self.sectionName} section.')
            self.set_key_value(self.sectionName, entryName, '')
            raise
        if prefix == '':
            raise ValueError(f'The configuration entry for {entryName} was blank.')
    @prefix.setter
    def prefix(self, prefix):
        entryName = 'prefix'
        # if the entry is not a one character string
        if not (isinstance(prefix, str) and prefix.len == 1):
            raise TypeError('Prefix must be a single character string.')
        # add the UX settings pair to the UX section
        self.set_key_value(self.sectionName, 'prefix', prefix)

    @property
    def owner(self):
        entryName = 'owner'
        # if the config is missing the UX section
        if not self._config.has_section(self.sectionName):
            # add the UX section to the config
            self.add_section(self.sectionName)
        # try to get the entry from the config file
        try:
            owner = self.get_key_value(self.sectionName, entryName)
        except ValueError as valueError:
            print(f'{valueError}\nA blank configuration entry has been created in the {self.sectionName} section for {entryName}.')
            self.set_key_value(self.sectionName, entryName, '')
            raise
        if owner == '':
            raise ValueError(f'The configuration entry for {entryName} was blank.')
    @owner.setter
    def owner(self, owner): 
        entryName = 'owner'
        # if the entry is not a string or integer
        if not isinstance(owner, str) and not isinstance(owner, int):
            raise TypeError(f'{entryName} configuration entry must be a numeric string or an integer.')
        # try to parse the entry to an integer
        try:
            owner = int(owner)
        # if entry cannot be parsed to an integer
        except NameError as nameError:
            raise TypeError(f'Configuration entry for {entryName} cannot be parsed to an integer.')
        # add the UX settings pair to the UX section
        self.set_key_value(self.sectionName, entryName, owner)

    @property
    def modules(self):
        entryName = 'modules'
        # if the config is missing the UX section
        if not self._config.has_section(self.sectionName):
            # add the UX section to the config
            self.add_section(self.sectionName)
        try:
            # get the folder name from the config file
            modules = self.get_key_value(self.sectionName, entryName)
            # if the modules key is empty
            if modules == '':
                raise TypeError(f'Entry for {entryName} was empty.')
            # get a Path instance from the provided string path
            path = pathlib.Path(modules)
            # if the path doesn't exist
            if not path.exists():
                # create the directory if it doesn't exist
                path.mkdir(parents=True, exist_ok=True)
            return modules
        except (ValueError, TypeError) as error:
            raise
    @modules.setter
    def modules(self, modules):
        entryName = 'modules'
        # get a Path instance from the provided string path
        path = pathlib.Path(modules)
        # if the path doesn't exist
        if not path.exists():
            # create the directory if it doesn't exist
            path.mkdir(parents=true, exist_ok=true)
        # add the modules path to the UX section
        self.set_key_value(self.sectionName, entryName, modules)