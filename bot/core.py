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
        try:
            return self._uxStore.modules
        except ValueError as valueError:
            self._uxStore.set_key_value(self._uxStore.sectionName, 'modules', '')
            missingModules = ' '.join([
                f'No modules entry found.',
                'An entry has been created for you to insert the modules path.'
            ])
            raise ValueError(missingModules)
        except TypeError as typeError:
            emptyToken = ' '.join([
                f'The modules entry contained an empty string.',
                'Please insert a modules path.'
            ])
            raise TypeError(typeError)
    @modules.setter
    def modules(self, modules):
        self._uxStore.modules = modules

    @property
    def mode(self):
        try:
            return self._tokenStore.mode
        except ValueError as valueError:
            self._tokenStore.add_token('mode', '')
            missingMode = ' '.join([
                f'No token mode entry found.',
                'An entry has been created for you to insert the token mode.'
            ])
            raise ValueError(missingMode)
        except TypeError as typeError:
            emptyToken = ' '.join([
                f'The token mode entry contained an empty string.',
                'Please insert a token mode.'
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