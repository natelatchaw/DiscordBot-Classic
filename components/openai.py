from typing import List, Optional, Union

from context import Context
from discord import Client, Member, User
from router.configuration import Section
from settings.settings import Settings

import openai
from openai.openai_object import OpenAIObject


class OpenAI():

    @property
    def key(self) -> str:
        key: str = 'key'
        value: Optional[str] = None
        try:
            value = self._config[key]
            if value and isinstance(value, str):
                return value
        except:
            self._config[key] = ""
            return None


    @property
    def is_enabled(self) -> bool:
        key: str = "enabled"
        value: Optional[str] = None
        try:
            value = self._config[key]
        except KeyError:
            self._config[key] = ""

        if value and isinstance(value, str):
            return value.lower() == str(True).lower()
        else:
            return False
    @is_enabled.setter
    def is_enabled(self, value: bool) -> None:
        key: str = "enabled"
        self._config[key] = str(value)


    def __init__(self, *args, **kwargs) -> None:
        try:
            self._client: Client = kwargs['client']
            self._settings: Settings = kwargs['settings']
        except KeyError as error:
            raise Exception(f'Key {error} was not found in provided kwargs', error)

        self.__setup__()

    def __setup__(self) -> None:
        key: str = self.__class__.__name__
        # create a config section for Audio
        self._settings[key] = Section(key, self._settings._parser, self._settings._reference)
        # create reference to Audio config section
        self._config: Section = self._settings[key]
        #
        openai.api_key = self.key

    async def prompt(self, context: Context, *, content: str, model: str = 'text-davinci-002', max_tokens: Union[str, int] = 128) -> None:
        print(content)
        if not self.is_enabled: raise ValueError(f'This command has been disabled in configuration.')
        user: Union[User, Member] = context.message.author
        id: int = hash(user.id)
        max_tokens = max_tokens if isinstance(max_tokens, int) else int(max_tokens)
        content = content.strip()
        completion: OpenAIObject = openai.Completion.create(model=model, prompt=content, echo=True, max_tokens=max_tokens, user=str(id))
        print(completion.to_dict_recursive())
        responses: List = completion.choices
        response: str = responses.pop(0).text
        block_tag: str = '```'
        await context.message.reply(f'{block_tag}\n{response}\n{block_tag}')
