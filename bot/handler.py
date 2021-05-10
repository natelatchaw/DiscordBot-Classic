import asyncio
import pathlib
import inspect
import collections
import importlib.util
import re
from bot.archiver import Archiver
from bot.core import Core
from bot.logger import Logger
from bot.module import ModuleInterface, InvalidInitializerError, InvalidCommandError

class Handler():
    def __init__(self):        
        # map command names to module names
        self._commands: dict[str, str] = dict()
        # map module names to modules
        self._modules: dict[str, ModuleInterface] = dict()

    def load(self, modules_folder: pathlib.Path=None):
        try:
            if not modules_folder:
                raise TypeError('Could not determine modules folder.')
            else:
                modules_path = pathlib.Path(modules_folder).resolve()
                print(f'Looking for modules in {modules_path}...')
        except (TypeError, ValueError):
            raise

        # get all python file paths in the modules directory
        modules: list[pathlib.Path] = [module for module in modules_path.glob('*.py') if module.is_file()]
        # for each python file path
        for module in modules:
            try:
                packaged_module: ModuleInterface = self.package(module)
                self.add(packaged_module)
            except ModuleNotFoundError as moduleNotFoundError:
                print(f'Failed to load {module.name}: {moduleNotFoundError}')
            except InvalidInitializerError as invalidInitializerError:
                print(invalidInitializerError)
            
    def package(self, module: pathlib.Path) -> ModuleInterface:
        # get module spec from module name and path
        spec = importlib.util.spec_from_file_location(module.stem, module.resolve())
        # create the module from the spec
        created_module = importlib.util.module_from_spec(spec)
        # execute the created module
        spec.loader.exec_module(created_module)
        # get each class member in the module (excluding classes imported from other modules)
        members = [member for member in inspect.getmembers(created_module, inspect.isclass) if member[1].__module__ == created_module.__name__]
        # get the name and class object for each class member
        for module_name, module_class in members:
            # create and return ModuleInterface
            return ModuleInterface(module_name, module_class)

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

    async def process(self, prefix: str, message: str, *, optionals: dict=dict()):

        # filter non-string message parameters
        if not isinstance(message, str):
            raise TypeError(f'Cannot process object that is not of type {type(str)}')

        # try to parse a command from the message
        try:
            command_prefix: str = prefix

            # get command from message
            command_match: re.Match = re.match(rf'^{command_prefix}[\w]+', message)
            # if the prefixed command could not be found at the beginning of the message
            if not command_match:
                raise TypeError(f'Message does not begin with prefix ({command_prefix})')
            # get the prefixed command string from the match
            prefixed_command: str = command_match.group()
            # remove prefix from command
            command_name: str = re.sub(rf'^{command_prefix}', '', prefixed_command)

            parameter_prefix = '-'
            # compile regex for parameter/argument pairs
            parameter_argument_pair: re.Pattern = re.compile(rf'{parameter_prefix}[\w]+[\s]+[\w\d\s<!@>]+\b')
            prefixed_parameter: re.Pattern = re.compile(rf'^{parameter_prefix}')

            # find all substrings that start with the parameter prefix and have arguments
            parameter_matches = re.findall(parameter_argument_pair, message)
            # strip the parameter prefix from each parameter/argument combo
            parameter_matches = [re.sub(prefixed_parameter, '', parameter_match) for parameter_match in parameter_matches]
            # strip any mention strings down to the author's id
            parameter_matches = [re.sub(r'<@!', '', parameter_match) for parameter_match in parameter_matches]
            # split the argument/parameter combo into tuple(parameter, argument)
            arguments = [tuple(parameter_match.split(maxsplit=1)) for parameter_match in parameter_matches]
            # convert list of tuples to dictionary
            kwargs = { argument[0] : argument[1] for argument in arguments }

            # create args list
            args = list()

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
                raise handlerError

            except TypeError as typeError:
                raise CommandHandlingError(command_name, typeError)

            except InvalidCommandError as invalidCommandError:
                raise invalidCommandError
        
        # if a valid command could not be parsed from the message
        except TypeError:
            # do nothing
            pass
            

class HandlerError(Exception):
    """Base exception class for the Handler class."""
    pass

class LookupError(HandlerError):
    """Base exception class for command lookup-related errors."""
    pass

class CommandHandlingError(HandlerError):
    """Raised when an exception occurs during the handling of a command."""

    def __init__(self, command_name: str, typeError: TypeError):
        self.command_name = command_name
        self.typeError = typeError

    def __str__(self):
        return f'Error in {self.command_name} command: {self.typeError}'

class CommandLookupError(LookupError):
    """Raised when the commands dict returns a KeyError when looking up a command name."""

    def __init__(self, command_name):
        self.command_name = command_name

    def __str__(self):
        return f'Could not find specified command: {self.command_name}.'

class ModuleLookupError(LookupError):
    """Raised when the modules dict returns a KeyError when looking up a module name."""

    def __init__(self, module_name):
        self.module_name = module_name

    def __str__(self):
        return f'Could not find specified module: {self.module_name}.'