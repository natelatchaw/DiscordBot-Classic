import os
import configparser
from configparser import DuplicateSectionError
import pathlib

class Configuration():
    def __init__(self):
        self._config = configparser.ConfigParser()
        self.file = os.path.abspath(f'config.ini')

        if not os.path.exists(self.file):
            with open(self.file, 'w') as configFile:
                self._config.write(configFile)

        self._config.read(self.file)

    def get_config(self):
        return self._config

    def reload(self):
        self._config.read(self.file)

    def add_section(self, section):
        """
        Adds the given section to the config file.
        Raises:
            TypeError if the section parameter is not a string
            DuplicateSectionError if a section already exists with the name contained in the section parameter
        """
        try:
            self._config.add_section(section)
            self.write()
        # if the section name is not a string
        except TypeError:
            raise TypeError(f'Cannot add section {section}: {section} is not a string value.')
        # if the default section name is passed
        except ValueError:
            pass
        # if a section name that already exists is passed
        except DuplicateSectionError:
            raise DuplicateSectionError(f'Cannot add section {section}: {section} already exists.')

    def set_key_value(self, section, key, value):
        """
        Sets a value for the given key in the given section.
        """
        try:
            # set the section name to all caps
            section = section.upper()
            self.add_section(section)
        except (ValueError, DuplicateSectionError):
            # pass if the section already exists
            pass
        finally:
            self._config.set(section, key, value)
            self.write()

    def get_key_value(self, section, key):
        """
        Retrieves the value for the given key in the given section.
        Raises:
            ValueError if the section does not contain the given key.
        """
        # reload the config file to get changes
        self.reload()
        # get the value for the provided key if it exists, or None if not
        value = self._config.get(section, key, fallback=None)
        # if the key does not exist in the config file
        if value is None:
            raise ValueError(f'Config file does not contain a key in section {section} for key: {key}.')
        # otherwise return value
        else:
            return value
            
    def write(self):
        with open(self.file, 'w') as configFile:
            self._config.write(configFile)

    def get_integer(self, section: str, key: str) -> int:
        # if the config is missing the given section
        if not self._config.has_section(section):
            # add the given section to the config
            self.add_section(section)
        try:
            # get the value from the config file
            value = self.get_key_value(section, key)
        except ValueError:
            # create the key if it is missing
            self.set_key_value(section, key, '')
            value = None
        try:
            # if the key's value is empty
            if not value:
                raise ValueError(f'Value for {key} is empty.')
            # parse the value to an integer or raise ValueError
            return int(value)
        except ValueError:
            raise

    def set_integer(self, section: str, key: str, value: int):
        # if the value is not an integer
        if not isinstance(value, int):
            raise ValueError(f'The {key} key must be of type {int}.')
        # add the given value to the given key in the given section
        self.set_key_value(section, key, str(value))

    def get_folder(self, section: str, key: str) -> str:
        # if the config is missing the given section
        if not self._config.has_section(section):
            # add the given section to the config
            self.add_section(section)
        try:
            # get the value from the config
            value = self.get_key_value(section, key)
        except ValueError:
            # create the key if it is missing
            self.set_key_value(section, key, '')
            value = None
        try:
            # if the key's value is missing
            if not value:
                raise ValueError(f'Entry for {key} is empty.')
            # get a Path instance from the given folder name
            path = pathlib.Path(value)
            # if the path doesn't exist
            if not path.exists():
                # create the directory
                path.mkdir(parents=True, exist_ok=True)
            return value
        except ValueError:
            raise

    def set_folder(self, section: str, key: str, value: str):
        # get a Path instance from the provided string path
        path = pathlib.Path(value)
        # if the path doesn't exist
        if not path.exists():
            # create the directory
            path.mkdir(parents=True, exist_ok=True)
        # add the given value to the given key in the given section
        self.set_key_value(section, key, value)

    def get_character(self, section: str, key: str):
        try:
            value = self.get_string(section, key)
            if not (isinstance(value, str) and len(value) == 1):
                raise ValueError(f'The value for {key} must be a single character.')
            return value
        except ValueError:
            raise

    def set_character(self, section: str, key: str, value: str):
        # if the given value is not a character
        if not (isinstance(value, str) and len(value) == 1):
            raise ValueError(f'The value for {key} must be a single character.')
        # add the given value to the given key in the given section
        self.set_string(section, key, value)

    def get_string(self, section: str, key: str):
        # if the config is missing the given section
        if not self._config.has_section(section):
            # add the given section to the config
            self.add_section(section)
        try:
            # get the value from the config
            value = self.get_key_value(section, key)
        except ValueError:
            # create the key if it is missing
            self.set_key_value(section, key, '')
            value = None
        try:
            # if the key's value is missing
            if not value:
                raise ValueError(f'Entry for {key} is empty')
            return value
        except ValueError:
            raise

    def set_string(self, section: str, key: str, value: str):
        # add the given value to the given key in the given section
        self.set_key_value(section, key, value)

