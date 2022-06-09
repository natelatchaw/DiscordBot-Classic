
import asyncio
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from sqlite3 import Cursor
from sys import argv
from time import process_time
import time
from typing import List, Optional, Pattern, Text, Tuple
from markovify import NewlineText

import discord
import markovify
import nltk
from context import Context
from discord import Guild, TextChannel, User, Message
from providers.channelArchive import ChannelArchive

url_pattern: Pattern = re.compile(r"(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))")
mention_pattern: Pattern = re.compile(r"<(?::\w+:|@!*&*|#)[0-9]+>")

def clean(text: str) -> str:
    text = text.lower()
    text = text.encode('ascii', 'ignore').decode()
    text = re.sub(url_pattern, '', text)
    text = re.sub(mention_pattern, '', text)
    text = re.sub(r'\t', '', text)
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'\[\]\`', '', text)
    text = text.strip()
    return text

class POSifiedText(markovify.NewlineText):
    def word_split(self, sentence):
        words = re.split(self.word_split_pattern, sentence)
        words = [ "::".join(tag) for tag in nltk.pos_tag(words) ]
        return words

    def word_join(self, words):
        sentence = " ".join(word.split("::")[0] for word in words)
        return sentence

class Generation():
    """
    
    """

    def __init__(self, *args, **kwargs):
        self._root: Path = Path('./archive/models')
        nltk.download('averaged_perceptron_tagger')

    def __save__(self, guild: Guild, channel: TextChannel, user: User, data: str) -> None:
        directory: Path = self._root
        directory = directory.joinpath(str(guild.id))
        directory = directory.joinpath(str(channel.id))
        directory = directory.resolve()
        if not directory.exists(): directory.mkdir(parents=True, exist_ok=True)
        file: Path = directory.joinpath(str(user.id))
        if not file.exists(): file.touch(exist_ok=True)
        file.write_text(data)

    def __load__(self, guild: Guild, channel: TextChannel, user: User) -> str:
        directory: Path = self._root
        directory = directory.joinpath(str(guild.id))
        directory = directory.joinpath(str(channel.id))
        directory = directory.resolve()
        if not directory.exists(): directory.mkdir(parents=True, exist_ok=True)
        file: Path = directory.joinpath(str(user.id))
        if not file.exists(): raise ValueError(f'No model found for {user.name}! Run \'compile\' to compile one.')
        return file.read_text()


    async def compile(self, context: Context) -> None:

        message: Message = await context.message.reply('Compiling...')

        guild: Guild = context.message.guild
        channel: TextChannel = context.message.channel
        user: User = context.message.author

        try:
            mention: Optional[User] = context.message.mentions.pop(0)
            if mention: user = mention
        except IndexError:
            pass

        archive: ChannelArchive = context.archive[guild.id][channel.id]

        start: float = process_time()

        sql: str = '''
        SELECT * FROM Messages
        WHERE AuthorID = ?
        '''
        parameters: Tuple = (user.id, )

        archive._cursor.execute(sql, parameters)
        rows: List[sqlite3.Row] = archive._cursor.fetchall()
        texts: List[str] = [row['content'] for row in rows]

        texts = [clean(text) for text in texts]
        texts = [text for text in texts if text]
        text: str = '\n'.join(texts)

        model: POSifiedText = POSifiedText(text)
        json: str = model.to_json()
        self.__save__(guild, channel, user, json)

        finish: float = process_time()

        delta: float = finish - start

        await message.edit(content=f'Compiled model for {user.mention} in {"%.2f" % delta}s')


    async def generate(self, context: Context, *, tries: int = 10) -> None:

        guild: Guild = context.message.guild
        channel: TextChannel = context.message.channel
        user: User = context.message.author

        try:
            mention: Optional[User] = context.message.mentions.pop(0)
            if mention: user = mention
        except IndexError:
            pass

        json: str = self.__load__(guild, channel, user)
        model: POSifiedText = POSifiedText.from_json(json)
        sentence: Optional[str] = model.make_sentence(tries=int(tries))
        if not sentence: 
            raise ValueError('Could not generate content; not enough source data. Try increasing value of the `-tries` flag (default 10).')
        
        embed: discord.Embed = discord.Embed()
        embed.set_author(name=user.name, icon_url=user.avatar_url)
        embed.description = sentence
        embed.timestamp = datetime.now(tz=timezone.utc)

        response: Message = await channel.send(embed=embed)
        


