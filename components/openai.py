from collections import defaultdict
import logging
import re
import textwrap
from logging import Logger
from math import ceil
from pathlib import Path
import traceback
from typing import DefaultDict, Dict, List, Literal, Optional, Union

from context import Context
from database.database import Database
from discord import Client, Embed, Member, Message, User
from router.configuration import Section
from settings.settings import Settings

import openai
from components.models.openai import Submission
from openai.openai_object import OpenAIObject

log: Logger = logging.getLogger(__name__)

MAX_MESSAGE_SIZE: Literal[2000] = 2000
"""
The maximum amount of characters
permitted in a Discord message
"""

# define model costs
MODEL_COSTS: Dict[str, float] = {
    'text-davinci-002': 0.0600 / 1000,
    'text-curie-001':   0.0060 / 1000,
    'text-babbage-001': 0.0012 / 1000,
    'text-ada-001':     0.0008 / 1000,
}

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
        #
        await self.__store__(context, submission=submission)

        # return the responses
        return responses

    async def __store__(self, context: Context, *, submission: Submission) -> None:
        # create the database
        self._database.create(Submission)
        # insert the submission
        self._database.insert(submission)

    async def __load__(self, context: Context) -> List[Submission]:
        # create the database
        self._database.create(Submission)
        # get all submissions
        submissions: List[Submission] = [Submission.__from_row__(row) for row in self._database.select(Submission)]
        # return submissions
        return submissions
    
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

    async def __get_tokens__(self, submission: Submission) -> int:
        # split the prompt by whitespace characters
        prompt_segments: List[str] = re.split(r"[\s]+", submission.prompt)
        # get a token count for each word
        prompt_token_counts: List[int] = [ceil(len(prompt_segment) / 4) for prompt_segment in prompt_segments]

        # split the response by whitespace characters
        response_segments: List[str] = re.split(r"[\s]+", submission.prompt)
        # get a token count for each word
        response_token_counts: List[int] = [ceil(len(response_segment) / 4) for response_segment in response_segments]

        # return the sum of token counts
        return sum(prompt_token_counts) + sum(response_token_counts)

    async def __get_cost__(self, submission: Submission, costs: Dict[str, float]) -> float:
        try:
            # retrieve the cost per token for the model used by the submission
            cost_per_token: float = costs[submission.model]
            # calculate the total cost
            total_cost: float = submission.token_count * cost_per_token
            # return the cost
            return total_cost
        except KeyError as error:
            log.warning(f'No cost defined for model {error}')
            return float(0)


    async def cost(self, context: Context) -> None:
        # load all submissions
        submissions: List[Submission] = await self.__load__(context)
        # get the message's author
        user: Union[User, Member] = context.message.author
        # get all submissions by the user
        submissions = [submission for submission in submissions if submission.user_id == user.id]

        # initialize a dictionary
        per_model: Dict[str, List[Submission]] = dict()
        # for each submission
        for submission in submissions:
            # if the per_model dictionary does not have the model as a key
            if not per_model.get(submission.model):
                # add the model as a key with a list
                per_model[submission.model] = list()
            # append the submission to the list for the submission's model
            per_model[submission.model].append(submission)

        embed: Embed = Embed()
        embed.title = 'OpenAI Usage'
        embed.set_author(name=user.name, icon_url=user.avatar_url)

        print(len(per_model))

        # for each entry in per_model
        for model, model_submissions in per_model.items():
            # calculate the cost for each submission
            costs: List[float] = [await self.__get_cost__(submission, MODEL_COSTS) for submission in model_submissions]
            # add the cost data to the embed
            embed.add_field(name=model, value=f'${sum(costs):0.2f} ({len(costs)} submission{"s" if len(costs) != 1 else ""})')

        await context.message.reply(embed=embed)

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

