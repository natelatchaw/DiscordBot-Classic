import re
import textwrap
from math import ceil
from pathlib import Path
from typing import List, Literal, Optional, Union

from context import Context
from database.database import Database
from discord import Client, Member, Message, User
from router.configuration import Section
from settings.settings import Settings

import openai
from components.models.openai import Submission
from openai.openai_object import OpenAIObject

MAX_MESSAGE_SIZE: Literal[2000] = 2000
"""
The maximum amount of characters
permitted in a Discord message
"""

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
        # set the api key
        openai.api_key = self.key
        # create database instance
        self._database: Database = Database(Path('./archive/openai.db'))

    async def __send__(self, context: Context, *, prompt: str, model: str = 'text-davinci-002', tokens: Union[int, str] = 128, echo: bool = False) -> List[str]:
        # check enabled configuration parameter
        if not self.is_enabled: raise ValueError('This command has been disabled.')
        # get the message's author
        user: Union[User, Member] = context.message.author
        # hash an ID from the author's ID
        id: int = hash(user.id)
        # convert the tokens parameter to an int if not already an int
        tokens = tokens if isinstance(tokens, int) else int(tokens)
        # create the Completion request
        completion: OpenAIObject = openai.Completion.create(model=model, prompt=prompt, max_tokens=tokens, echo=echo, user=str(id))

        # get the list of choices
        choices: List[OpenAIObject] = completion.choices
        # get the list of text responses
        responses: List[str] = [choice.text for choice in choices]
        
        # calculate the total token count
        token_count: int = sum([await self.__get_tokens__(response) for response in responses])
        # create submission object
        submission: Submission = Submission(context.message.id, user.id, model, prompt, '###'.join(responses), token_count)
        # create the database
        self._database.create(submission)
        # insert the submission
        self._database.insert(submission)

        # return the responses
        return responses
    
    async def __print__(self, context: Context, *, responses: List[str]):
        # define the block tag for code block messages
        block_tag: str = '```'
        # for each returned response
        for response in responses:
            # calculate the max characters that can be inserted into each message's code block
            max_characters: int = MAX_MESSAGE_SIZE - (2 * len(block_tag))
            # break the response into string segments with length equivalent to the maximum character limit
            segments: List[str] = textwrap.wrap(response, max_characters, break_long_words=False, replace_whitespace=False)
            # set the initial message reference to the original message
            message: Message = context.message
            # for each segment
            for segment in segments:
                # send the message and set the message reference to the sent message
                message = await message.reply(f'{block_tag}\n{segment}\n{block_tag}')

    async def __get_tokens__(self, content: str) -> int:
        # split the provided string by whitespace characters
        segments: List[str] = re.split(r"[\s]+", content)
        # get a token count for each word
        token_counts: List[int] = [ceil(len(segment) / 4) for segment in segments]
        # return the sum of token counts
        return sum(token_counts)

    async def prompt(self, context: Context, *, content: str, model: str = 'text-davinci-002', tokens: Union[str, int] = 128) -> None:
        # send the prompt
        responses: List[str] = await self.__send__(context, prompt=content, model=model, tokens=tokens, echo=False)
        # send the responses
        await self.__print__(context, responses=responses)

    async def write(self, context: Context, *, a: Optional[str] = None, about: Optional[str] = None, model: str = 'text-davinci-002', tokens: Union[str, int] = 128) -> None:
        # initialize a list for content strings
        content: List[str] = list()
        # seed the prompt with the greentext prompt
        content.append('write')
        # append the value
        if a: content.append(f'a {a}')
        # append the value
        if about: content.append(f'about {about}')
        # join the content by spaces
        prompt: str = ' '.join(content)
        # send the prompt
        responses: List[str] = await self.__send__(context, prompt=prompt, model=model, tokens=tokens, echo=False)
        # send the responses
        await self.__print__(context, responses=responses)

    async def greentext(self, context: Context, *, be_me: Optional[str] = None, model: str = 'text-davinci-002', tokens: Union[str, int] = 256) -> None:
        # initialize a list for content strings
        content: List[str] = list()
        # seed the prompt with the greentext prompt
        content.append(textwrap.dedent('''
            generate a 4chan greentext

            >Be me
        '''))
        # if a be_me parameter was provided
        if be_me:
            # append the value
            content.append('>' + be_me)
        # join the content by newlines
        prompt: str = '\n'.join(content)
        # send the prompt
        responses: List[str] = await self.__send__(context, prompt=prompt, model=model, tokens=tokens, echo=True)
        # send the responses
        await self.__print__(context, responses=responses)

