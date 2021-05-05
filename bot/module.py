import types
import asyncio
import inspect
from inspect import Signature, BoundArguments
from bot.core import Core
from bot.command import CommandInterface

class ModuleInterface():

    def __init__(self, name: str, obj: object):
        # get the signature of the object's initializer
        initializer_signature: Signature = inspect.signature(obj.__init__)
        # if the initializer requires more parameters than self
        if len(initializer_signature.parameters) > 1:
            # raise error
            raise InvalidInitializerError(name)

        # set module name
        self.name = name
        # instantiate obj and store
        self.instance = obj()
        # instantiate commands dictionary
        self.commands: dict[str, Signature] = dict()
        # get each method member in the class instance
        members = [member for member in inspect.getmembers(self.instance, inspect.ismethod)]
        # iterate over all methods in the class instance
        for name, member in members:
            # if method is a dunder method
            if name.startswith('__'):
                pass
            # otherwise
            else:
                # insert name, signature pair into commands dictionary
                self.commands[name] = CommandInterface(name, member)
        # get the docstring for the class
        self.doc = obj.__doc__

        print(f'Loaded {len(self.commands)} commands from {self.name} module.')

    def get_command_signature(self, command_name: str) -> Signature:
        """
        Retrieve a command signature from the command module.

        Parameters:
            command_name: str - the command's name

        Note:
            Annotated types can be retreived from signatures, if available.
            for parameter in signature.parameters.values():
                print(parameter.annotation)
        """
        # try to get the signature from the commands dictionary
        try:
            command: CommandInterface = self.commands[command_name]
            return command.signature
        # if the module doesn't contain a command named 'command_name'
        except KeyError:
            raise InvalidCommandError(self.name, command_name)

    def get_command_callable(self, command_name: str) -> types.MethodType:
        """
        Retrieve a command callable from the command module.

        Parameters:
            command_name: str - the command's name
        """
        # try to get the command from the module instance
        try:
            return getattr(self.instance, command_name)
        # if the module doesn't contain a command named 'command_name'
        except AttributeError:
            raise InvalidCommandError(self.name, command_name)

    async def run_command(self, command_name: str, arguments: BoundArguments):
        """
        Run the command given the name and the arguments.
        """
        try:
            # get the command's callable
            command = self.get_command_callable(command_name)
            # the the command's signature
            signature = self.get_command_signature(command_name)
        # if the module doesn't contain a command named 'command_name'
        except InvalidCommandError:
            raise

        # if the provided argument's signature does not match
        if arguments.signature.parameters != signature.parameters:
            raise ParameterMismatchError(signature, arguments.signature)

        # if the called command is synchronous
        if Command.isSynchronousMethod(command):
            # call command with parameters
            command(*arguments.args, **arguments.kwargs)

        # not supported yet
        if Command.isAsynchronousMethod(command):
            await command(*arguments.args, **arguments.kwargs)
    


class ModuleError(Exception):
    """Base exception class for command module exceptions."""
    pass

class InvalidInitializerError(ModuleError):
    """Raised when a module class is provided that requires initialization parameters."""

    def __init__(self, module_name: str):
        self.module_name = module_name

    def __str__(self):
        return f'Module {self.module_name} requires initialization parameters, which are not supported.'

class InvalidCommandError(ModuleError):
    """Raised when an attempt to access a non-existent command is made."""
    
    def __init__(self, module_name, command_name):
        self.module_name = module_name
        self.command_name = command_name

    def __str__(self):
        return f'Command {self.command_name} does not exist in module {self.module_name}.'

class ParameterMismatchError(ModuleError):
    """Raised when arguments provided to a command do not match its signature."""
    
    def __init__(self, command_signature: Signature, argument_signature: Signature):
        self.command_signature = command_signature
        self.argument_signature = argument_signature

    def __str__(self):
        return f'''Invalid arguments provided to command. Expected {self.command_signature}; received {self.argument_signature}.'''


class Command():
    @classmethod
    def isSynchronousMethod(cls, obj):
        return inspect.ismethod(obj) and not inspect.iscoroutinefunction(obj)

    @classmethod
    def isAsynchronousMethod(cls, obj):
        return inspect.ismethod(obj) and inspect.iscoroutinefunction(obj)