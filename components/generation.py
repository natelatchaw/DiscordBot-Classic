import time
from operator import length_hint
import random
from typing import Dict, List, Set, Tuple
import discord
from discord import message
from nltk.stem.wordnet import WordNetLemmatizer
import numpy
from providers.archiver import Archiver
import nltk
from nltk.corpus import stopwords

class Generation():

    def __init__(self):
        if not nltk.download(info_or_id='all', download_dir='./nltk', quiet=True):
            raise Exception('Failed to download NLTK data.')
        nltk.data.path.append('./nltk')

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
        corpus: str = '\n'.join(user_messages)

        lemmatizer: WordNetLemmatizer = WordNetLemmatizer()
        stop_words: Set[str] = set(stopwords.words('english'))

        
        tokens: List[str] = nltk.sent_tokenize(corpus, language='english')
        tokens: List[str] = [lemmatizer.lemmatize(word=word.lower()) for word in tokens if word not in stop_words]
        tokens: List[str] = [word.lower() for word in tokens if len(word) > 1]

        print(tokens)

        return
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

        print(generated)
        print(message_content)

        await _message.channel.send(message_content)

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