import os
import sys
import time
from importlib import import_module
import configparser
import discord
import random
import inspect

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
    # set status to online
    await client.change_presence(status = discord.Status.online)
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
    if random.random() < 0.01:
        await channel.send(f'{pre} {user.mention} {post}')

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
        except ValueError:
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
            command_instance.client = client
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
