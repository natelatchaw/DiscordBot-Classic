import random
import time
from datetime import datetime
from typing import Dict, List, Set, Tuple

import discord
import nltk
import numpy
from nltk.corpus import stopwords, wordnet
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.tag import pos_tag
from providers.archiver import Archiver


class Generation_():

    def __init__(self):
        print(f'Attempting to update NLTK data...')
        if not nltk.download(info_or_id='all', download_dir='./nltk', quiet=True):
            raise Exception('Failed to update NLTK data.')
        else:
            print(f'Updated NLTK data.')
        nltk.data.path.append('./nltk')

    async def emulate(self, *, _message: discord.Message, _archiver: Archiver, user: str = None):
        await _archiver.fetch()

        try:
            user_id: int = int(user)
            members: List[discord.Member] = _message.guild.members
            author: discord.Member = [member for member in members if member.id == user_id].pop(0)
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
            try:
                filtered_words = [word for word, word_count in potential_words.items() if (dictionary.get(word))]
                selected_word: str = numpy.random.choice(filtered_words)
                next_word: str = selected_word
                generated.append(next_word)
            except ValueError:
                next_word = None
        
        message_content: str = ' '.join(generated)
        message_content = message_content[:1999]

        embed: discord.Embed = discord.Embed()
        embed.set_author(name=author.display_name, icon_url=author.avatar_url)
        embed.description = message_content
        embed.timestamp = datetime.now()

        await _message.channel.send(embed=embed)

    async def emulate_beta(self, *, _message: discord.Message, _archiver: Archiver, user: str = None):
        await _archiver.fetch()

        lemmatizer: WordNetLemmatizer = WordNetLemmatizer()
        part_of_speech_tags: Dict[str, wordnet.ADJ|wordnet.NOUN|wordnet.VERB|wordnet.ADV] = { 'J': wordnet.ADJ, 'N': wordnet.NOUN, 'V': wordnet.VERB, 'R': wordnet.ADV }
        stop_words: Set[str] = set(stopwords.words('english'))

        try:
            user_id: int = int(user)
            members: List[discord.Member] = _message.guild.members
            author: discord.Member = [member for member in members if member.id == user_id].pop(0)
        except NameError:
            await _message.channel.send(f'{user} is not a valid user.')
            return

        messages: List[Tuple[int, str]] = await _archiver.select(['AUTHOR_ID', 'CONTENT'])
        user_messages: List[str] = [content for author_id, content in messages if user_id == author_id]
        
        tokenized_messages: List[str] = [nltk.word_tokenize(user_message, language='english') for user_message in user_messages]
        tagged_tokenized_messages: List[List[Tuple(str, str)]] = [pos_tag(tokenized_message) for tokenized_message in tokenized_messages]
        lemmatized_messages: List[List[str]] = [[lemmatizer.lemmatize(word=word.lower(), pos=part_of_speech_tags.get(part_of_speech[0], wordnet.NOUN)) for word, part_of_speech in tagged_tokenized_message if word.isalpha()] for tagged_tokenized_message in tagged_tokenized_messages]
        lemmatized_messages: List[List[str]] = [[lemmatized_token for lemmatized_token in lemmatized_message if lemmatized_token not in stop_words] for lemmatized_message in lemmatized_messages]

        dictionary: Dict[str, Dict[str, int]] = dict()

        for row in lemmatized_messages:
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
            try:
                filtered_words = [word for word, word_count in potential_words.items() if (dictionary.get(word))]
                selected_word: str = numpy.random.choice(filtered_words)
                next_word: str = selected_word
                generated.append(next_word)
            except ValueError:
                next_word = None
        
        message_content: str = ' '.join(generated)
        message_content = message_content[:1999]

        embed: discord.Embed = discord.Embed()
        embed.set_author(name=author.display_name, icon_url=author.avatar_url)
        embed.description = message_content
        embed.timestamp = datetime.now()

        await _message.channel.send(embed=embed)

    async def corpus(self, *, _message: discord.Message):
        try:
            sentences: List[List[str]] = [' '.join(sentence) for sentence in nltk.corpus.gutenberg.sents('shakespeare-caesar.txt')]
            # sentences: List[str] = nltk.sent_tokenize(nltk.corpus.gutenberg.words('shakespeare-caesar.txt'))
            for sentence in sentences:
                time.sleep(1)
                print(sentence)
                await _message.channel.send(sentence)
        except TypeError as exception:
            raise
