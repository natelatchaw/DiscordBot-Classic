import re

from discord import Guild, TextChannel
import markovify
import nltk


class POSifiedText(markovify.NewlineText):
    def word_split(self, sentence: str):
        words = re.split(self.word_split_pattern, sentence)
        words = [ "::".join(tag) for tag in nltk.pos_tag(words) ]
        return words

    def word_join(self, words: str):
        sentence = " ".join(word.split("::")[0] for word in words)
        return sentence

    
class ChannelUser:
    def __init__(self, guild: Guild, channel: TextChannel) -> None:
        self.id: int = channel.id
        self.name: str = channel.name
        self.avatar_url: str = guild.icon_url
        self.mention: str = channel.mention