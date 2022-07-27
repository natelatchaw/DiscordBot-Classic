from typing import List, Optional, Tuple

from discord import Embed, Message
from context import Context

emoji_list: List[str] = ['🇦', '🇧', '🇨', '🇩', '🇪', '🇫', '🇬', '🇭']

class Poll():
    """
    """

    def __init__(self, *args, **kwargs):
        pass

    async def poll(self, context: Context, *, options: str, title: Optional[str] = None, description: Optional[str] = None, image: Optional[str] = None):

        option_list: List[str] = [option.strip() for option in options.split(',')]

        if len(option_list) > len(emoji_list): raise ValueError(f'Up to {len(emoji_list)} options are supported.')
        
        zipped_list: zip[Tuple[str, str]] = zip(emoji_list, option_list)
        available_options: List[Tuple[str, str]] = list(zipped_list)

        embed: Embed = Embed()
        embed.title = title
        embed.description = description
        embed.set_author(name=context.message.author.display_name, icon_url=context.message.author.avatar_url)

        for option in available_options:
            embed.add_field(name=f'Option {option[0]}', value=option[1], inline=False)

        embed.timestamp = context.message.created_at

        if image: embed.set_thumbnail(url=image)

        poll_message: Message = await context.message.channel.send(embed=embed)

        for option in available_options:
            await poll_message.add_reaction(option[0])