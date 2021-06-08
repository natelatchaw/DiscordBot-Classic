from datetime import datetime, time, timezone
from typing import Dict
import discord
from router.command import Command
from router.component import Component

class Info:
    """
    Provides information about the client.
    """

    def __init__(self):
        pass

    async def about(self, *, _message: str, _components: Dict[str, Component], _features: Dict[str, str], _instantiated_time: datetime):
        embed = discord.Embed()

        embed.title = 'About'

        embed.add_field(name='Uptime', value=str((datetime.now(tz=timezone.utc) - _instantiated_time)))

        features: list(str) = [acronym for acronym, name in _features.items()]
        embed.add_field(name='Handler Features', value='\n'.join(features), inline=False)

        components: list(str) = [name for name, component in _components.items()]
        embed.add_field(name='Loaded Components', value='\n'.join(components), inline=False)

        embed.timestamp = _instantiated_time
        await _message.channel.send(embed=embed)

    async def help(self, *, _message: str, _components: dict, component: str=None):
        """
        Provides usage data for commands.

        Parameters:
            -component: specify a component to retrieve help data for
        """
        embed = discord.Embed()
        if component:
            try:
                targetModule = _components[component]
                embed.title = targetModule.name
                embed.description = targetModule.doc
                for command in targetModule.commands.items():
                    command_name: str = command[0]
                    command: Command = command[1]
                    if command.doc:
                        embed.add_field(name=command_name, value=command.doc, inline=False)
                    else:
                        embed.add_field(name=command_name, value='Command documentation unavailable', inline=False)
                embed.timestamp = time()
            except KeyError:
                await _message.channel.send(f'Could not find a component named **{component}**')
                return

        else:
            embed.title = "Help"
            embed.description = self.__doc__
            for name, component in _components.items():
                if component.doc:
                    embed.add_field(name=component.name, value=component.doc, inline=False)
                else:
                    embed.add_field(name=component.name, value='Component documentation unavailable', inline=False)
            embed.timestamp = time()

        await _message.channel.send(embed=embed)