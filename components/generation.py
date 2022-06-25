import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from time import process_time
from typing import List, Optional, Pattern, Tuple, Union

import discord
import markovify
import nltk
from context import Context
from discord import ClientUser, Guild, Member, Message, TextChannel, User
from providers.channelArchive import ChannelArchive
from settings.settings import Settings

nltk.download('averaged_perceptron_tagger', quiet=True)

class POSifiedText(markovify.NewlineText):
    def word_split(self, sentence):
        words = re.split(self.word_split_pattern, sentence)
        words = [ "::".join(tag) for tag in nltk.pos_tag(words) ]
        return words

    def word_join(self, words):
        sentence = " ".join(word.split("::")[0] for word in words)
        return sentence

    
class ChannelUser:
    def __init__(self, guild: Guild, channel: TextChannel) -> None:
        self.id: int = channel.id
        self.name: str = channel.name
        self.avatar_url: str = guild.icon_url
        self.mention: str = channel.mention


class Generation():
    """
    """

    def __init__(self, *args, **kwargs):
        self._root: Path = Path('./archive/models')
        self.__compile_regex__()

        try:
            self._client: discord.Client = kwargs['client']
            self._settings: Settings = kwargs['settings']
        except KeyError as error:
            raise Exception(f'Key {error} was not found in provided kwargs')

    def __compile_regex__(self) -> None:
        """
        Compile regex patterns used in message analyzation.
        """
        
        # compile the url pattern
        self._url_pattern: Pattern = re.compile(r"(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))")
        # compile the mention pattern
        self._mention_pattern: Pattern = re.compile(r"<(?::\w+:|@!*&*|#)[0-9]+>")


    def __clean__(self, text: str) -> str:
        """
        Cleans the text of any irregular characters
        """

        text = text.lower()
        text = text.encode('ascii', 'ignore').decode()
        text = re.sub(self._url_pattern, '', text)
        text = re.sub(self._mention_pattern, '', text)
        text = re.sub(r'\n', ' ', text)
        text = re.sub(r'\t', '', text)
        text = re.sub(r'\[', '', text)
        text = re.sub(r'\]', '', text)
        text = text.strip()
        return text


    def __save__(self, guild: Guild, channel: TextChannel, user: User, data: str) -> None:
        """
        Saves the text data to the directory dictated by the guild, channel and user parameters
        """

        directory: Path = self._root
        directory = directory.joinpath(str(guild.id))
        directory = directory.joinpath(str(channel.id))
        directory = directory.resolve()
        if not directory.exists(): directory.mkdir(parents=True, exist_ok=True)
        file: Path = directory.joinpath(str(user.id))
        if not file.exists(): file.touch(exist_ok=True)
        file.write_text(data)

    def __load__(self, guild: Guild, channel: TextChannel, user: User) -> str:
        """
        Loads the text data from the directory dictated by the guild, channel and user parameters
        """

        directory: Path = self._root
        directory = directory.joinpath(str(guild.id))
        directory = directory.joinpath(str(channel.id))
        directory = directory.resolve()
        if not directory.exists(): directory.mkdir(parents=True, exist_ok=True)
        file: Path = directory.joinpath(str(user.id))
        if not file.exists(): raise ValueError(f'No model found for {user.mention}\nRun \'compile\' to compile one.')
        return file.read_text()


    async def __get_target__(self, context: Context) -> Optional[Union[User, Member, ClientUser, ChannelUser]]:

        message: Message = await context.message.reply('Compiling...')

        guild: Guild = context.message.guild
        channel: TextChannel = context.message.channel
        user: Optional[Union[User, Member, ClientUser, ChannelUser]] = None

        try:
            user = context.message.mentions.pop(0)
        except IndexError:
            # user = context.message.author
            user = ChannelUser(guild, channel)
        
        return user


    async def compile(self, context: Context) -> None:

        guild: Guild = context.message.guild
        channel: TextChannel = context.message.channel

        user: Optional[Union[User, Member, ClientUser, ChannelUser]] = await self.__get_target__(context)
        archive: ChannelArchive = context.archive[guild.id][channel.id]

        message: Message = await context.message.reply('Compiling...')

        start: float = process_time()

        select: str = '''
        SELECT * FROM Messages
        '''
        where: str = '''
        WHERE AuthorID = ?
        '''
        sql = f'{select} {where}' if user else f'{select}'        
        parameters: Tuple = (user.id, ) if user else ()

        archive._cursor.execute(sql, parameters)
        rows: List[sqlite3.Row] = archive._cursor.fetchall()
        texts: List[str] = [row['content'] for row in rows]

        texts = [self.__clean__(text) for text in texts]
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

        user: Optional[Union[User, Member, ClientUser, ChannelUser]] = await self.__get_target__(context)
        archive: ChannelArchive = context.archive[guild.id][channel.id]

        json_str: str = self.__load__(guild, channel, user)
        model: POSifiedText = POSifiedText.from_json(json_str)
        sentence: Optional[str] = model.make_sentence(tries=int(tries))
        if not sentence: 
            raise ValueError('Could not generate content; not enough source data. Try increasing value of the `-tries` flag (default 10).')
        
        embed: discord.Embed = discord.Embed()
        embed.set_author(name=user.name, icon_url=user.avatar_url)
        embed.description = sentence
        embed.timestamp = datetime.now(tz=timezone.utc)

        response: Message = await channel.send(embed=embed)

    
    async def talk(self, context: Context, *, about: str, tries: Union[int, str] = 10, loops: Union[int, str] = 1000) -> None:

        guild: Guild = context.message.guild
        channel: TextChannel = context.message.channel

        user: Optional[Union[User, Member, ClientUser, ChannelUser]] = await self.__get_target__(context)
        archive: ChannelArchive = context.archive[guild.id][channel.id]

        json_str: str = self.__load__(guild, channel, user)
        model: POSifiedText = POSifiedText.from_json(json_str)

        loop: int = 0
        loops = loops if isinstance(loops, int) else int(loops)
        tries = tries if isinstance(tries, int) else int(tries)

        attempt: Optional[str] = None
        sentence: Optional[str] = None
        
        while loop < loops:
            loop = loop + 1
            attempt = model.make_sentence(tries=int(tries))
            if not attempt:
                continue
            elif about.lower() not in attempt.lower():
                continue
            else:
                sentence = attempt
                break
        
        if not sentence:
            raise ValueError(f'Could not find content containing {about} in {loops} attempts.')
        
        embed: discord.Embed = discord.Embed()
        embed.set_author(name=user.name, icon_url=user.avatar_url)
        embed.description = sentence
        embed.timestamp = datetime.now(tz=timezone.utc)
        
        if self._settings.ux.verbose:
            embed.add_field(name='attempt', value=f'{loop}/{loops}')

        response: Message = await channel.send(embed=embed)

        


