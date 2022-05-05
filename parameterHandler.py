import pathlib
import re
from typing import Dict, List, Tuple
from router.component import Component
from router.error.component import ComponentError
from router.error.handler import HandlerError, HandlerPrefixError
from router.handler import Handler


class ParameterHandler(Handler):

    @property
    def features(self) -> Dict[str, str]:
        return {
            'HDKI': 'Hyphen Delimited Keyword Injection',
            'SDDMI': 'Single Directory Dynamic Module Import',
        }
    
    def __init__(self):
        super().__init__()

    def load(self, components_folder: pathlib.Path):
        return super().load(components_folder)

    def package(self, module: pathlib.Path) -> List[Component]:
        return super().package(module)

    def add(self, component: Component):
        return super().add(component)

    def get(self, command_name: str) -> Component:
        return super().get(command_name)

    async def run(self, command_name: str, args: List, kwargs: Dict[str, str], optionals: Dict[str, object]):
        return await super().run(command_name, args=args, kwargs=kwargs, optionals=optionals)

    async def process(self, prefix: str, message: str, *, optionals: Dict[str, object]):
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
                raise HandlerPrefixError(prefix, ValueError('Message to process does not begin with expected prefix.'))
            # get the prefixed command string from the match
            prefixed_command: str = command_match.group()
            # remove prefix from command
            command_name: str = re.sub(rf'^{command_prefix}', '', prefixed_command)

            parameter_prefix = '-'
            # compile regex for parameter/argument pairs
            parameter_argument_pair: re.Pattern = re.compile(rf'{parameter_prefix}[\w]+[\s]+(?:(?!\s\-).)*\b')
            ##parameter_argument_pair: re.Pattern = re.compile(rf'{parameter_prefix}[\w]+[\s]+[\w\d\s<!@>?\#\=\:\/\.]+\b')
            prefixed_parameter: re.Pattern = re.compile(rf'^{parameter_prefix}')

            # find all substrings that start with the parameter prefix and have arguments
            parameter_matches: List[str] = re.findall(parameter_argument_pair, message)
            # strip the parameter prefix from each parameter/argument combo
            parameter_matches: List[str] = [re.sub(prefixed_parameter, '', parameter_match) for parameter_match in parameter_matches]

            ### TODO: Factor out Discord-specific parameter manipulation
            ###
            # strip any user mention strings down to the author's id
            parameter_matches: List[str] = [re.sub(r'<@!', '', parameter_match) for parameter_match in parameter_matches]
            # strip any user mention strings down to the author's id (mobile)
            parameter_matches: List[str] = [re.sub(r'<@', '', parameter_match) for parameter_match in parameter_matches]
            # strip any voice channel mention strings down to the channel's id
            parameter_matches: List[str] = [re.sub(r'<#', '', parameter_match) for parameter_match in parameter_matches]
            ###
            ###

            # split the argument/parameter combo into tuple(parameter, argument)
            arguments: List[Tuple[str]] = [tuple(parameter_match.split(maxsplit=1)) for parameter_match in parameter_matches]
            # convert list of tuples to dictionary
            kwargs: Dict[str, str] = { argument[0] : argument[1] for argument in arguments }

            # create args list
            args: List = list()
            # run the command
            await self.run(command_name, args, kwargs, optionals)

        # if the message doesn't start with a prefix
        except HandlerPrefixError:
            return
        except (HandlerError, ComponentError):
            raise