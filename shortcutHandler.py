from parameterHandler import ParameterHandler
import pathlib
import re
from typing import Dict, List, Tuple
from router.component import Component
from router.error.component import ComponentError
from router.error.handler import HandlerError, HandlerPrefixError
from router.handler import Handler

class Shortcut():
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def command_name(self) -> str:
        return self._command_name

    @property
    def parameter(self) -> str:
        return self._parameter

    def __init__(self, name, command_name, parameter) -> None:
        self._name = name
        self._command_name = command_name
        self._parameter = parameter

class ShortcutHandler(Handler):

    @property
    def features(self) -> Dict[str, str]:
        return {
            'HDKI': 'Hyphen Delimited Keyword Injection',
            'SDDMI': 'Single Directory Dynamic Module Import',
            'SCDR': 'Shortcut-Command Dynamic Replacement',
        }

    @property
    def shortcuts(self) -> List[Shortcut]:
        return self._shortcuts
    
    def __init__(self, shortcuts: List[Shortcut]):
        self.parameterHandler = ParameterHandler()
        self._shortcuts = shortcuts
        super().__init__()

    def load(self, components_folder: pathlib.Path):
        return self.parameterHandler.load(components_folder=components_folder)

    def package(self, module: pathlib.Path) -> List[Component]:
        return self.parameterHandler.package(module)

    def add(self, component: Component):
        return self.parameterHandler.add(component)

    def get(self, command_name: str) -> Component:
        return self.parameterHandler.get(command_name)

    async def run(self, command_name: str, args: List, kwargs: Dict[str, str], optionals: Dict[str, object]):
        return await self.parameterHandler.run(command_name, args, kwargs, optionals=optionals)

    async def process(self, prefix: str, message: str, *, optionals: Dict[str, object]):
        try:
            command_prefix: str = prefix

            # get command from message
            command_match: re.Match = re.match(rf'^{command_prefix}[\w]+', message)
            # if the prefixed command could not be found at the beginning of the message
            if not command_match:
                raise HandlerPrefixError(prefix, ValueError('Message to process does not begin with expected prefix.'))
            # get the prefixed command string from the match
            prefixed_command: str = command_match.group()
            # remove prefix from command
            command_name: str = re.sub(rf'^{command_prefix}', '', prefixed_command)

            # tuple of the command passed (e.g., ['play', 'what is love'])
            command_parts: Tuple[str, str] = tuple(message.split(maxsplit=1))
            # get list of shortcut commands matching the message command
            shortcuts: List[Shortcut] = [shortcut for shortcut in self.shortcuts if shortcut.name == command_name]
            # if the list of shortcuts is of nonzero length
            if len(shortcuts):
                # get the first shortcut
                shortcut: Shortcut = shortcuts.pop()
                # create and assemble kwargs
                kwargs: Dict[str, str] = dict()
                kwargs[shortcut.parameter] = command_parts[1]
                # run shortcutted command with kwargs
                await self.parameterHandler.run(shortcut.command_name, args=list(), kwargs=kwargs, optionals=optionals)
            else:
                # default to parameter handling
                await self.parameterHandler.process(prefix, message, optionals=optionals)

        
        # if the message doesn't start with a prefix
        except HandlerPrefixError:
            return
        except (HandlerError, ComponentError):
            raise
