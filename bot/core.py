import os
import discord
import inspect
from .configuration.tokenstore import TokenStore
from .configuration.uxstore import UXStore

class Core():
    def __init__(self, tag):
        self._tag = tag
        self._tokenStore = TokenStore()
        self._uxStore = UXStore()

    @property
    def prefix(self):
        return self._uxStore.prefix
    @prefix.setter
    def prefix(self, prefix):
        self._uxStore.prefix = prefix

    @property
    def token(self):
        try:
            return self._tokenStore.get_token(self._tag)
        except ValueError as valueError:
            print(valueError)
            self._tokenStore.add_token(self._tag, 'INSERT TOKEN HERE')
            missingToken = ' '.join([
                f'No entry found with tag <{self._tag}>. ',
                'An entry has been created for you to insert your token.'
            ])
            print(missingToken)
            raise valueError
        except TypeError as typeError:
            emptyToken = ' '.join([
                f'Entry with tag <{self._tag}> contained an empty string.',
                'Please insert a token for sign-in.'
            ])
            print(emptyToken)
            raise typeError
    @token.setter
    def token(self, token):
        self._tokenStore.add_token(self._tag, token)