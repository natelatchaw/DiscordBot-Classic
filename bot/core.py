import discord
import inspect
from bot.configuration import Configuration

class Core():
    def __init__(self, client, prefix, tag):
        self._prefix = prefix
        self._tag = tag
        self._client = client
        self._config = Configuration()

    @property
    def client(self):
        return self._client

    @property
    def prefix(self):
        return self._prefix
    @prefix.setter
    def set_prefix(self, prefix):
        # make sure the prefix is a string of length 1
        if not isinstance(prefix, str) and prefix.len != 1:
            raise TypeError('Prefix must be a single character string.')
        self._prefix = prefix

    @property
    def token(self):
        token = self._config.get_token(self._tag)
        if token is None:
            self._config.add_token(self._tag, 'INSERT TOKEN HERE')
            self._config.write_out()
            missingToken = ' '.join([
                f'No entry found with tag <{self._tag}>. ',
                'An entry has been created for you to insert your token.'
            ])
            print(missingToken)
            self._client.stop()
        else:
            return token
    @token.setter
    def set_token(self, token):
        self._config.add_token(self._tag, token)




    async def start(self):
        print(f'Connecting...')
        await self._client.start(self._token)

    async def stop(self):
        print(f'Disconnecting...')
        await self.client.stop()
