from operator import length_hint
import random
from typing import Counter, Dict, List, Tuple
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
        array: List[List[str]] = [content.split() for content in user_messages]

        dictionary: Dict[str, Dict[str, int]] = dict()

        for row in array:
            # for each word in the message
            for word in range(len(row) - 1):
                # get the current word
                current_word: str = row[word]
                # get the next word
                next_word: str = row[word + 1]
                # if there isn't already an entry for the current word
                if current_word not in dictionary.keys():
                    # create an empty list to put the next word in
                    dictionary[current_word] = dict()
                # if there isn't already an entry for the next word in the current word dict
                if next_word not in dictionary[current_word].keys():
                    # set the next word count to 1
                    dictionary[current_word][next_word] = 1
                # if there is already an entry for the next word in the current word dict
                elif next_word in dictionary[current_word].keys():
                    # increment the next word count by 1
                    dictionary[current_word][next_word] += 1

        length: int = random.randint(8, 20)
        generated: List[str] = [numpy.random.choice(list(dictionary.keys()))]

        while next_word is not None and len(generated) < 15:
            previous_word: str = generated[-1]
            potential_words: Dict[str, int] = dictionary.get(previous_word)
            filtered_words = [word for word, word_count in potential_words.items() if (dictionary.get(word))]
            selected_word: str = numpy.random.choice(filtered_words)
            next_word: str = selected_word
            generated.append(next_word)
        
        message_content: str = ' '.join(generated)

        print(generated)
        print(message_content)

        await _message.channel.send(message_content)




        
