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
    def owner(self):
        # if the config is missing the UX section
        if not self._config.has_section(self.sectionName):
            # add the UX section to the config
            self.add_section(self.sectionName)
        try:
            # get the owner id value from the config file
            owner = self.get_key_value(self.sectionName, 'owner')
        except ValueError as valueError:
            print(valueError)
            print(f'A blank entry for owner has been created in the {self.sectionName} section.')
            self.set_key_value(self.sectionName, 'owner', '')
            raise
        try:
            if owner == '':
                raise TypeError(f'Entry for owner was empty.')
            return owner
        except (ValueError, TypeError) as error:
            print(error)
    @owner.setter
    def owner(self, owner): 
        # make sure the prefix is a string
        if not isinstance(owner, str) and not isinstance(owner, int):
            raise TypeError('Owner ID must be a numeric string or an integer.')
        # try to parse the owner parameter to an integer
        try:
            owner = int(owner)
        # if owner parameter cannot be parsed to an integer
        except NameError as nameError:
            raise TypeError('Provided owner ID cannot be parsed to an integer.')
        # add the UX settings pair to the UX section
        self.set_key_value(self.sectionName, 'owner', owner)

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