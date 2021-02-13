import os
import configparser


class Configuration():
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.file = os.path.abspath('./config.ini')

        if not os.path.exists(self.file):
            self.config['DEFAULT'] = {'prefix':'', 'console_spacing':''}
            self.config['TOKENS'] = {'development':'', 'production':''}
            self.config['DEVELOPMENT'] = {'enabled':''}
            self.config['MODULES'] = {'enabled':'', 'folder':''}
            self.config['LOGGING'] = {'enabled':'', 'folder':'', 'module':''}
            self.config['TYPING'] = {'pre':'', 'post':''}
            with open(self.file, 'w') as configFile:
                self.config.write(configFile)

        self.config.read(self.file)

    def get_config(self):
        return self.config

    def reload(self):
        self.config.read(self.file)

    def add_keypair(self, section, key, value):
        self.config[section][key] = value

    def get_key_value(self, section, key):
        return self.config[section][key]

    def add_token(self, name, token):
        # if there is no [TOKENS] section
        if not 'TOKENS' in self.config:
            # create the [TOKENS] section
            self.config['TOKENS'] = {}
        # set a key and value in the 'TOKENS' section
        self.config['TOKENS'][name] = str(token)

    def get_token(self, name):
        if not 'TOKENS' in self.config:
            self.config['TOKENS'] = {}
        return self.config['TOKENS'].get(name)

    def set_module_mode(self, enabled):
        # set the mode contained in the 'config.ini' file's module mode key
        self.config['MODULES']['enabled'] = str(enabled)

    def get_module_mode(self):
        # get the mode contained in the 'config.ini' file's module mode key
        try:
            return self.config.getboolean('MODULES', 'enabled', fallback = False)
        except ValueError:
            print('Configuration file is missing values. Exiting...')
            exit()

    def set_development_mode(self, enabled):
        # set the mode contained in the 'config.ini' file's development mode key
        self.config['DEVELOPMENT']['enabled'] = str(enabled)

    def get_development_mode(self):
        # get the mode contained in the 'config.ini' file's development mode key
        try:
            return self.config.getboolean('DEVELOPMENT', 'enabled', fallback = False)
        except ValueError:
            print('Configuration file is missing values. Exiting...')
            exit()

    def set_logging_mode(self, enabled):
        # set the mode contained in the 'config.ini' file's logging mode key
        self.config['LOGGING']['enabled'] = str(enabled)

    def get_logging_mode(self):
        # get the mode contained in the 'config.ini' file's logging mode key
        try:
            return self.config.getboolean('LOGGING', 'enabled', fallback = False)
        except ValueError:
            print('Configuration file is missing values. Exiting...')
            exit()

    def set_prefix(self, prefix):
        self.config['DEFAULT']['prefix'] = str(prefix)

    def get_prefix(self):
        return self.config.get('DEFAULT', 'prefix', fallback = '/')

    def set_console_spacing(self, spacing):
        self.config['DEFAULT']['console_spacing'] = spacing

    def get_console_spacing(self):
        return self.config.get('DEFAULT', 'console_spacing', fallback = 16)

    def write_out(self):
        with open(self.file, 'w') as configFile:
            self.config.write(configFile)
