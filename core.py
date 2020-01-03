import os
import sys
import time
from importlib import import_module
import configparser
import discord
import random

class Core():
    def __init__(self, prefix, token):
        self.prefix = prefix
        self.token = token
        self.client = discord.Client()

    def setPrefix(self, prefix):
        self.prefix = prefix

    def setLastMessage(self, message):
        self.lastMessage = message

    def getLastMessage(self):
        if self.lastMessage:
            return self.lastMessage
        else:
            return None

class Configuration():
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.file = os.path.abspath('./config.ini')

        if not os.path.exists(self.file):
            self.config['DEFAULT'] = {'prefix':'', 'console_spacing':''}
            self.config['TOKENS'] = {'development':'', 'release':''}
            self.config['DEVELOPMENT'] = {'enabled':''}
            self.config['MODULES'] = {'enabled':'', 'folder':''}
            self.config['LOGGING'] = {'enabled':'', 'folder':'', 'module':''}
            self.config['TYPING'] = {'pre':'', 'post':''}
            with open(self.file, 'w') as configFile:
                self.config.write(configFile)

        self.config.read(self.file)

    def getConfig(self):
        return self.config

    def reload(self):
        self.config.read(self.file)

    def addKeypair(self, section, key, value):
        self.config[section][key] = value

    def getKeyValue(self, section, key):
        return self.config[section][key]

    def addToken(self, name, token):
        # if there is no [TOKENS] section
        if not 'TOKENS' in self.config:
            # create the [TOKENS] section
            self.config['TOKENS'] = {}
        # set a key and value in the 'TOKENS' section
        self.config['TOKENS'][name] = str(token)

    def getToken(self, name):
        if not 'TOKENS' in self.config:
            self.config['TOKENS'] = {}
        return self.config['TOKENS'][name]

    def setModuleMode(self, enabled):
        # set the mode contained in the 'config.ini' file's module mode key
        self.config['MODULES']['enabled'] = str(enabled)

    def getModuleMode(self):
        # get the mode contained in the 'config.ini' file's module mode key
        try:
            return self.config.getboolean('MODULES', 'enabled', fallback = False)
        except ValueError as valueError:
            print('Configuration file is missing values. Exiting...')
            exit()

    def setDevelopmentMode(self, enabled):
        # set the mode contained in the 'config.ini' file's development mode key
        self.config['DEVELOPMENT']['enabled'] = str(enabled)

    def getDevelopmentMode(self):
        # get the mode contained in the 'config.ini' file's development mode key
        try:
            return self.config.getboolean('DEVELOPMENT', 'enabled', fallback = False)
        except ValueError as valueError:
            print('Configuration file is missing values. Exiting...')
            exit()

    def setLoggingMode(self, enabled):
        # set the mode contained in the 'config.ini' file's logging mode key
        self.config['LOGGING']['enabled'] = str(enabled)

    def getLoggingMode(self):
        # get the mode contained in the 'config.ini' file's logging mode key
        try:
            return self.config.getboolean('LOGGING', 'enabled', fallback = False)
        except ValueError as valueError:
            print('Configuration file is missing values. Exiting...')
            exit()

    def setPrefix(self, prefix):
        self.config['DEFAULT']['prefix'] = str(prefix)

    def getPrefix(self):
        return self.config.get('DEFAULT', 'prefix', fallback = '/')

    def setConsoleSpacing(self, spacing):
        self.config['DEFAULT']['console_spacing'] = spacing

    def getConsoleSpacing(self):
        return self.config.get('DEFAULT', 'console_spacing', fallback = 16)

    def writeOut(self):
        with open(self.file, 'w') as configFile:
            self.config.write(configFile)

class Console():
    def __init__(self, configuration):
        self.consoleSpacing = configuration.getConsoleSpacing()

    def output(self, string):
        tag = 'Console'
        output_string = f'{tag:{self.consoleSpacing}}{string}'
        print(output_string)

# initialize configuration instance
configuration = Configuration()
# initialize console instance
console = Console(configuration)

if configuration.getDevelopmentMode():
    # get development token and setup
    core = Core(configuration.getPrefix(), configuration.getToken('development'))
    core.mode = 'development'
elif not configuration.getDevelopmentMode():
    # get production token and setup
    core = Core(configuration.getPrefix(), configuration.getToken('release'))
    core.mode = 'release'
client = core.client


@client.event
async def on_ready():
    print(f'Logged on as {client.user}: using {core.mode} token')
    print(f'Dev mode active: {configuration.getDevelopmentMode()}')
    print(f'Logging enabled: {configuration.getLoggingMode()}')
    print(f'CWD: {os.getcwd()}')
    guilds = []
    for guild in core.client.guilds:
        guilds.append(guild.name)
    guilds_string = (', '.join(guilds))
    print(f'Guilds: [{guilds_string}]')
    print('\n')

@client.event
async def on_typing(channel, user, time):
    pre = configuration.getKeyValue('TYPING', 'pre')
    post = configuration.getKeyValue('TYPING', 'post')
    if random.random() < 10.01:
        await channel.send(f'{pre} {user.display_name} {post}')

@client.event
async def on_message(message):
    core.setLastMessage(message)
    # log message
    print(f'{str(message.author):{configuration.getConsoleSpacing()}}{str(message.clean_content)}')

    # if the message's author is the bot
    if message.author == client.user:
        return

    # module launcher
    # reload config file
    configuration.reload()
    # get prefix from config file
    prefix = configuration.getKeyValue('DEFAULT', 'prefix')
    # check if the first [len(core.prefix)] characters of the message begin with the prefix
    if message.content[:len(prefix)] == prefix and configuration.getModuleMode():
        # remove prefix from text and split to list
        args = message.content[len(prefix):].split()
        # get first list element (the command)
        command_name = args.pop(0)

        try:
            moduleFolder = configuration.getKeyValue('MODULES', 'folder')
        except ValueError as valueError:
            print('Configuration file is missing the module folder value. Exiting...')
            exit()

        try:
            # get module matching the string in command variable
            module = import_module(f'{moduleFolder}.{command_name.title()}')
            # get class with same name as module from the module
            command = getattr(module, command_name.title())
            # instantiate the class
            command_instance = command(args)
            # set instance attributes
            command_instance.message = message
            command_instance.prefix = prefix
            command_instance.configuration = configuration
            command_instance.console = console
            # run the instance's run method
            returned_data = await command_instance.run()
            if returned_data is not None:
                await message.channel.send(returned_data)
        except ModuleNotFoundError as moduleNotFoundError:
            await message.channel.send(f'Command not found: {command_name.title()}')
        except AttributeError as attributeError:
            print(f'Attribute error for module {command_name.title()}: {attributeError}')

    # message logger; runs only if message does not start with prefix
    elif configuration.getLoggingMode():
        try:
            # get the folder and module names from 'config.ini'
            loggingFolder = configuration.getKeyValue('LOGGING', 'folder')
            loggingModule = configuration.getKeyValue('LOGGING', 'module')
        except ValueError as valueError:
            print('Configuration file is missing values. Exiting...')
            exit()

        try:
            # get logging module
            module = import_module(f'{loggingFolder}.{loggingModule}')
            # get logging class
            logger = getattr(module, loggingModule)
            logger = logger()
            logger.message = message
            logger.loggingFolder = loggingFolder
            await logger.run()
        except ModuleNotFoundError as moduleNotFoundError:
            print(f'Logging module {loggingModule} improperly installed')
            print(moduleNotFoundError)

try:
    client.run(core.token)
except discord.errors.LoginFailure as loginFailure:
    print(f'Invalid Token: {loginFailure}')
    exit()
