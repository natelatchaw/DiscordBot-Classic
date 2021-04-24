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
        return self._uxStore.owner
    @owner.setter
    def owner(self, owner):
        self._uxStore.owner = owner

    @property
    def modules(self):
        entry_name = 'modules'
        try:
            return self._uxStore.modules
        except ValueError:
            self._uxStore.set_key_value(self._uxStore.sectionName, entry_name, '')
            missingModules = ' '.join([
                f'No {entry_name} entry found.',
                f'An entry has been created for you to insert the {entry_name} path.'
            ])
            raise ValueError(missingModules)
        except TypeError:
            emptyToken = ' '.join([
                f'The {entry_name} entry contained an empty string.',
                f'Please insert a {entry_name} path.'
            ])
            raise TypeError(emptyToken)
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