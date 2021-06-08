from operator import length_hint
import random
from typing import Dict, List, Tuple
import discord
from discord import message
import numpy
from providers.archiver import Archiver

class Generation():

    def __init__(self):
        pass

    async def emulate(self, *, _message: discord.Message, _archiver: Archiver, user: str = None):
        print(user)
        channel: discord.TextChannel = _message.channel
        await _archiver.fetch()

        try:
            user_id: int = int(user)
        except NameError:
            await _message.channel.send(f'{user} is not a valid user.')
            return

        messages: List[Tuple[int, str]] = await _archiver.select(['AUTHOR_ID', 'CONTENT'])
        user_messages: List[str] = [content for author_id, content in messages if user_id == author_id]
        word_array: List[List[str]] = [content.split() for content in user_messages]

        dictionary: Dict[str, List[str]] = dict()
        for row in word_array:
            for word in range(len(row) - 1):
                # get the current word
                current_word: str = row[word]
                # get the next word
                next_word: str = row[word + 1]
                # if there isn't already an entry for the current word
                if current_word not in dictionary.keys():
                    # create an empty list to put the next word in
                    dictionary[current_word] = list()
                # put the next word into the list for the current word
                dictionary[current_word].append(next_word)

        length: int = random.randint(8, 20)
        generated: List[str] = [numpy.random.choice(list(dictionary.keys()))]
        for word in range(length):
            generated.append(numpy.random.choice(dictionary[generated[-1]]))
        
        message_content: str = ' '.join(generated)

        print(generated)
        print(message_content)

        await _message.channel.send(message_content)




        
