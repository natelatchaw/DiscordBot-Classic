import os
import configparser
from configparser import DuplicateSectionError

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
        try:
            self._config.add_section(section)
            self.write()
        # if the section name is not a string
        except TypeError:
            raise TypeError(f'Cannot add section {section}: {section} is not a string value.')
        # if the default section name is passed
        except ValueError:
            pass
            # bypass the error below; useful for debugging purposes
            # raise ValueError(f'Cannot add section {section}: {section} is already the default section.')
        # if a section name that already exists is passed
        except DuplicateSectionError:
            raise DuplicateSectionError(f'Cannot add section {section}: {section} already exists.')

    def set_key_value(self, section, key, value):
        try:
            # set the section name to all caps
            section = section.upper()
            self.add_section(section)
        except (ValueError, DuplicateSectionError):
            ##print(f'Skipping {section} section creation during keypair add: section already exists.')
            pass
        finally:
            self._config.set(section, key, value)
            self.write()

    def get_key_value(self, section, key):
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
