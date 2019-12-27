import os
import sys
import time
from importlib import import_module
import configparser
import discord

class Core():
    def __init__(self, prefix, token):
        self.prefix = prefix
        self.token = token
        self.client = discord.Client()

    def setPrefix(self, prefix):
        self.prefix = prefix

class Configuration():
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.file = os.path.abspath('./config.ini')

        if not os.path.exists(self.file):
            self.config['DEFAULT'] = {'prefix':''}
            self.config['TOKENS'] = {'development':'', 'release':''}
            self.config['DEVELOPMENT'] = {'enabled':''}
            self.config['MODULES'] = {'enabled':'', 'folder':''}
            self.config['LOGGING'] = {'enabled':'', 'folder':'', 'module':''}
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

    def writeOut(self):
        with open(self.file, 'w') as configFile:
            self.config.write(configFile)

class Delay():
    def __init__(self, name):
        self.name = name
        self.start = time.time()

    def print(self):
        self.end = time.time()
        self.delta = ((self.end - self.start) * 1000)
        print('[%14.2fus] %s' % (self.delta, self.name))

configuration = Configuration()

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
    print('Logged on as <%s>: using %s token' % (client.user, core.mode))
    print('Dev Mode active: %s' % configuration.getDevelopmentMode())
    print('Logging enabled: %s' % configuration.getLoggingMode())
    print(os.getcwd())
    guilds = []
    for guild in core.client.guilds:
        guilds.append(guild.name)
    print('Guilds: [%s]' % (', '.join(guilds)))
    print('\n')
    # end counting delay for bot initialization and output to console
    initializationDelay.print()

@client.event
async def on_message(message):
    # log message
    print('<%16s> %s' % (str(message.author), str(message.clean_content)))

    # if the message's author is the bot
    if message.author == client.user:
        return

    # start counting delay for reading configuration file
    configReadDelay = Delay('Configuration file read time')
    # module launcher
    # reload config file
    configuration.reload()
    # end counting delay for reading configuration file and output to console
    configReadDelay.print()
    # get prefix from config file
    prefix = configuration.getKeyValue('DEFAULT', 'prefix')
    # check if the first [len(core.prefix)] characters of the message begin with the prefix
    if message.content[:len(prefix)] == prefix and configuration.getModuleMode():
        # remove prefix from text and split to list
        args = message.content[len(prefix):].split()
        # get first list element (the command)
        command = args.pop(0)

        moduleExecutionDelay = Delay('Module execution time')
        try:
            moduleFolder = configuration.getKeyValue('MODULES', 'folder')
        except ValueError as valueError:
            print('Configuration file is missing values. Exiting...')
            exit()

        try:
            # get module matching the string in command variable
            module = import_module('%s.%s' % (moduleFolder, command.title()))
            # get class with same name as module from the module
            command = getattr(module, command.title())
            # instantiate the class
            command = command(args)
            # set instance attributes
            command.message = message
            # run the instance's run method and send obtained data
            await message.channel.send(await command.run())
        except ModuleNotFoundError as moduleNotFoundError:
            await message.channel.send('Command not found: <%s>' % command)
        except AttributeError as attributeError:
            print('No module named <%s>' % command)

        moduleExecutionDelay.print()


    # message logger; runs only if message does not start with prefix
    elif configuration.getLoggingMode():
        # start counting delay for logging code
        loggingDelay = Delay('Message logging time')
        try:
            # get the folder and module names from 'config.ini'
            loggingFolder = configuration.getKeyValue('LOGGING', 'folder')
            loggingModule = configuration.getKeyValue('LOGGING', 'module')
        except ValueError as valueError:
            print('Configuration file is missing values. Exiting...')
            exit()

        try:
            # get logging module
            module = import_module('%s.%s' % (loggingFolder, loggingModule))
            # get logging class
            logger = getattr(module, loggingModule)
            logger = logger()
            logger.message = message
            logger.loggingFolder = loggingFolder
            await logger.run()
        except ModuleNotFoundError as moduleNotFoundError:
            print('Logging module <%s> improperly installed' % loggingModule)
            print(moduleNotFoundError)
        # end counting delay for logging code and output to console
        loggingDelay.print()

# start counting delay for bot initialization
initializationDelay = Delay('Initialization time')
try:
    client.run(core.token)
except discord.errors.LoginFailure as loginFailure:
    print('Invalid Token: %s' % loginFailure)
    exit()
