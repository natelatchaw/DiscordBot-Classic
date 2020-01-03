import os
from os import listdir
from importlib import import_module
import discord

class Help():
    def __init__(self, args):
        self.name = 'Help'
        self.description = 'Provides info about a module'
        self.syntax = ['help', 'help *command name*']
        self.args = args

    async def run(self):
        output = self.console.output
        try:
            # get config file data here
            self.moduleFolder = self.configuration.getKeyValue('MODULES', 'folder')
        except ValueError as valueError:
            output('Configuration file is missing module folder data.')
            await self.message.channel.send('A configuration error occurred. Ask the bot owner to check their console.')
            return

        # get list of commands in modules folder
        commands = await self.get_commands()

        # if the user provided any arguments
        if self.args:
            # for each argument provided
            for arg in self.args:
                try:
                    # check if command list contains arg, if not, throws ValueError
                    commands.index(arg.title())
                    command_instance = await self.get_command_instance(arg.title())

                    # convert syntax list to string and add prefix
                    syntax = ''
                    for example in command_instance.syntax:
                        syntax = syntax + f'{self.prefix}{example}\n'

                    # create embed object and populate with command data
                    embed = discord.Embed()
                    embed.title = command_instance.name
                    embed.description = command_instance.description
                    embed.add_field(name = '**Syntax**', value = syntax, inline = False)

                    # send embed object
                    await self.message.channel.send(embed = embed)

                except ValueError as valueError:
                    await self.message.channel.send(f'Could not find a command named **{arg}**')

        else:
            # initialize command_instances list
            command_instances = []
            for command in commands:
                # get command instance from command name
                command_instance = await self.get_command_instance(command)
                # add command_instance to command_instances
                command_instances.append(command_instance)

            # initialize embed object
            embed = discord.Embed()
            embed.title = 'Available commands'
            embed.description = f'For more information about a command, use **{self.prefix}help <command name>**'
            for command_instance in command_instances:
                embed.add_field(name = f'**{self.prefix}{command_instance.name}**', value = command_instance.description, inline = False)
            # send embed object
            await self.message.channel.send(embed = embed)

    async def get_command_instance(self, command_name):
        try:
            module = import_module(f'{self.moduleFolder}.{command_name.title()}')
            # get the module's class object
            command = getattr(module, command_name.title())
            # instantiate the class with a blank arg
            instance = command('')
            return instance
        except Exception as exception:
            print(exception)

    async def get_commands(self):
        # initialize command list
        commands = []
        # list all items in modules directory
        directory_contents = os.listdir(f'{os.getcwd()}/{self.moduleFolder}')
        # for each item in the modules directory
        for item in directory_contents:
            # get the item's name
            filename = os.path.basename(item)
            # if the item has the file extension '.py' and is not the __init__ file
            if os.path.splitext(filename)[-1] == '.py' and os.path.splitext(filename)[0] != '__init__':
                # add the command to the 'commands' list
                commands.append(os.path.splitext(filename)[0])

        return commands
