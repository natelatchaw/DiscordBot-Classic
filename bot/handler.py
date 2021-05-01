import asyncio
import pathlib
import inspect
import collections
import importlib.util
import discord
from bot.archiver import Archiver
from bot.core import Core
from bot.logger import Logger
from bot.module import ModuleInterface, InvalidInitializerError, InvalidCommandError

class Handler():
    def __init__(self, client: discord.Client, core: Core):
        if not isinstance(client, discord.Client):
            raise TypeError('Invalid client parameter passed.')
        else:
            self._client = client

        if not isinstance(core, Core):
            raise TypeError('Invalid core parameter passed.')
        else:
            self._core = core
        # create dictionary of archiver objects
        self._archivers = dict()
        
        # map command names to module names
        self._commands: dict(str, str) = dict()
        # map module names to modules
        self._modules: dict(str, ModuleInterface) = dict()

        self.load()

    def __del__(self):
        # for every channel archiver that was instantiated
        for archiver in self._archivers.values():
            archiver.close()

    def load(self):
        try:
            if self._core.modules is None:
                raise TypeError('Could not determine modules folder.')
            else:
                modules_path = pathlib.Path(self._core.modules).resolve()
                print(f'Looking for modules in {modules_path}...')
        except (TypeError, ValueError):
            raise

        # get all python file paths in the modules directory
        modules = [module for module in modules_path.glob('*.py') if module.is_file()]
        # for each python file path
        for module in modules:
            # get module spec from module name and path
            spec = importlib.util.spec_from_file_location(module.stem, module.resolve())
            # create the module from the spec
            created_module = importlib.util.module_from_spec(spec)
            # execute the created module
            spec.loader.exec_module(created_module)
            # get the name and class object for each class in the module
            for module_name, module_class in inspect.getmembers(created_module, inspect.isclass):
                try:
                    command_module = ModuleInterface(module_name, module_class)
                    self.add(command_module)
                except InvalidInitializerError as invalidInitializerError:
                    print(invalidInitializerError)

    def add(self, module: ModuleInterface):
        # for each command's name in the command module
        for command_name in module.commands.keys():
            # TODO: command_name not guaranteed to be unique across modules, overwriting is possible here
            # add the command-to-module mapping
            self._commands[command_name] = module.name
        # add the module-name-to-module mapping
        self._modules[module.name] = module

    def get(self, command_name: str) -> ModuleInterface:
        try:
            module_name = self._commands[command_name]
        except KeyError:
            raise CommandLookupError(command_name)
        try:
            module: ModuleInterface = self._modules[module_name]
        except KeyError:
            raise ModuleLookupError(module_name)
        return module

    async def archive(self, message: discord.Message) -> Archiver:
        # if an archiver instance hasn't been created for the current channel
        if message.channel.id not in self._archivers:
            # create an archiver instance
            archiver = Archiver(message.channel)
            # add the archiver instance to the archiver dict
            self._archivers[message.channel.id] = archiver
            print(f'Created archiver instance for channel {message.channel.id}')
        # if an archiver instance already exists for the current channel
        else:
            # get the archiver instance
            archiver = self._archivers[message.channel.id]
            print(f'Found archiver instance for channel {message.channel.id}')

        # create a table for the current channel if it hasn't been created yet
        await archiver.create()
        # insert the current message into the archiver
        await archiver.insert(message)
        # return the archiver instance
        return archiver


    async def process(self, message: discord.Message, *, optionals: dict=dict(), archiver_key: str=None):

        # filter non-message objects
        if not isinstance(message, discord.Message):
            raise TypeError(f'Cannot process object that is not of type {type(discord.Message)}')

        # if an archive key was provided
        if archiver_key:
            # insert the archiver into optionals dictionary
            optionals[archiver_key] = await self.archive(message)

        # try to parse a command from the message
        try:
            self._core.prefix
            # if the message doesn't start with the prefix
            if not message.clean_content.startswith(self._core.prefix):
                raise TypeError(f'Message does not begin with prefix ({self._core.prefix})')
            
            # get the cleaned content of the message
            content = message.clean_content
            # split by hyphen delimiter and strip whitespace
            arguments = [part.strip() for part in content.split('-')]
            # pop the first item as the command and strip the prefix
            command_name = arguments.pop(0).strip(self._core.prefix)
            # split each arg into keyword and value tuple
            arguments = [tuple(argument.split(maxsplit=1)) for argument in arguments]
            # convert list of tuples to dictionary
            kwargs = { argument[0] : argument[1] for argument in arguments if len(argument) == 2 }

            # add message to parameter arguments
            args = list()
            args.append(message)

            try:
                # try to get the relevant module
                module = self.get(command_name)
                # get the command's command signature
                command_signature = module.get_command_signature(command_name)
                
                # for each optional keyvalue pair passed in through contructor
                for optional_key, optional_value in optionals.items():
                    # if the command's signature contains a parameter matching the optional key
                    if optional_key in command_signature.parameters.keys():
                        # add the correlated optional value to kwargs
                        kwargs[optional_key] = optional_value

                # bind the processed arguments to the command signature
                bound_arguments = command_signature.bind(*args, **kwargs)
                # run the command with the assembled signature
                await module.run_command(command_name, bound_arguments)

            except HandlerError as handlerError:
                await message.channel.send(handlerError)

            except TypeError as typeError:
                await message.channel.send(f'Error in {command_name} command: {typeError}')

            except InvalidCommandError as invalidCommandError:
                await message.channel.send(invalidCommandError)
        
        # if a valid command could not be parsed from the message
        except TypeError:
            # fallback to console message log
            print(message.clean_content)
            

class HandlerError(Exception):
    """Base exception class for the Handler class."""
    pass

class LookupError(HandlerError):
    """Base exception class for command lookup-related errors."""
    pass

class CommandLookupError(LookupError):
    """Raised when the commands dict returns a KeyError when looking up a command name."""

    def __init__(self, command_name):
        self.command_name = command_name

    def __str__(self):
        return f'Could not find specified command: {self.command_name}.'

class ModuleLookupError(LookupError):
    """Raised when the moudles dict returns a KeyError when looking up a module name."""

    def __init__(self, module_name):
        self.module_name = module_name

    def __str__(self):
        return f'Could not find specified module: {self.module_name}.'