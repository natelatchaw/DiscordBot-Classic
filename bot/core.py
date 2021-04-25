import os
import discord
import inspect
from .configuration.tokenstore import TokenStore
from .configuration.uxstore import UXStore

class Core():
    def __init__(self):
        self._tokenStore = TokenStore()
        self._uxStore = UXStore()

    @property
    def prefix(self):
        return self._uxStore.prefix
    @prefix.setter
    def prefix(self, prefix):
        self._uxStore.prefix = prefix

    @property
    def owner(self):
        key = 'owner'
        try:
            return self._uxStore.owner
        except ValueError as valueError:
            invalidEntry = '\n'.join([
                str(valueError),
                f'Please insert a valid {key} id in the config file.'
            ])
            raise ValueError(invalidEntry)
    @owner.setter
    def owner(self, owner_id: int):
        self._uxStore.owner = owner_id

    @property
    def modules(self):
        entry_name = 'modules'
        try:
            return self._uxStore.modules
        except ValueError as valueError:
            invalidEntry = '\n'.join([
                str(valueError),
                f'Please insert a valid {entry_name} path in the config file.'
            ])
            raise ValueError(invalidEntry)
    @modules.setter
    def modules(self, modules):
        self._uxStore.modules = modules

    @property
    def mode(self):
        entry_name = 'mode'
        try:
            return self._tokenStore.mode
        except ValueError:
            self._tokenStore.mode = ''
            missingMode = ' '.join([
                f'No token {entry_name} selector was found in the config.',
                f'An selector entry has been created for you to specify the token {entry_name}.'
            ])
            raise ValueError(missingMode)
        except TypeError:
            emptyToken = ' '.join([
                f'The token {entry_name} selector in the config contained an empty string.',
                f'Please specify a token {entry_name}.'
            ])
            raise TypeError(emptyToken)
    @mode.setter
    def mode(self, mode):
        self._tokenStore.mode = mode

    @property
    def token(self):
        try:
            return self._tokenStore.get_token(self.mode)
        except ValueError as valueError:
            self._tokenStore.add_token(self.mode, 'INSERT TOKEN HERE')
            missingToken = ' '.join([
                f'No entry found with tag <{self.mode}>.',
                'An entry has been created for you to insert your token.'
            ])
            print(missingToken)
            raise valueError
        except TypeError as typeError:
            emptyToken = ' '.join([
                f'Entry with tag <{self.mode}> contained an empty string.',
                'Please insert a token for sign-in.'
            ])
            print(emptyToken)
            raise typeError
    @token.setter
    def token(self, token):
        self._tokenStore.add_token(self.mode, token)

    @property
    def logging_channel(self):
        entry_name = 'logging_channel'
        try:
            return self._uxStore.logging_channel
        except ValueError as valueError:
            invalidEntry = '\n'.join([
                str(valueError),
                f'Please insert a valid {entry_name} id in the config file.'
            ])
            raise ValueError(invalidEntry)
    @logging_channel.setter
    def logging_channel(self, channel_id: int):
        self._uxStore.logging_channel = channel_id