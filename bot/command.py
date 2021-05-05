import inspect
from inspect import Signature, BoundArguments

class CommandInterface():

    def __init__(self, name: str, command: object):
        # get the name of the command
        self.name = name
        # get the command's signature
        self.signature: Signature = inspect.signature(command)
        # get the command's docstring
        self.doc = command.__doc__

    @property
    def signature(self) -> Signature:
        return self._signature
    @signature.setter
    def signature(self, signature: Signature):
        self._signature = signature
