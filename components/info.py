from datetime import datetime, time, timezone
import imp
from typing import Dict, List
import discord
from router.command import Command
from router.component import Component
from router.registration import Registration

class Info:
    """
    Provides information about the client.
    """

    def __init__(self):
        pass

    async def about(self, *, _message: str, _components: List[Registration], _features: Dict[str, str], _instantiated_time: datetime):
        embed = discord.Embed()
        embed.title = 'About'

        embed.add_field(name='Uptime', value=str((datetime.now(tz=timezone.utc) - _instantiated_time)))

        features: List[str] = [acronym for acronym, name in _features.items()]
        embed.add_field(name='Handler Features', value='\n'.join(features), inline=False)

        components: List[str] = [component.command.name for component in _components]
        embed.add_field(name='Loaded Components', value='\n'.join(components), inline=False)

        embed.timestamp = _instantiated_time
        await _message.channel.send(embed=embed)

    async def help(self, *, _message: str, _components: List[Registration], component: str=None):
        """
        Provides usage data for commands.

        Parameters:
            -component: specify a component to retrieve help data for
        """
        embed = discord.Embed()
        if component:
            registrations: List[Registration] = [registration for registration in _components if registration.component.name.lower() == component.lower()]
            try:
                registration: Registration = registrations[0]
                embed.title = registration.component.name
                embed.description = registration.component.doc
                for command in registration.component.commands:
                    if command.doc:
                        embed.add_field(name=command.name, value=command.doc, inline=False)
                    else:
                        embed.add_field(name=command.name, value='Command documentation unavailable', inline=False)
                embed.timestamp = datetime.now(tz=timezone.utc)
            except IndexError:
                await _message.channel.send(f'Could not find a component named **{component}**')
                return

        else:
            embed.title = "Help"
            embed.description = self.__doc__
            for registration in _components:
                if registration.component.doc:
                    embed.add_field(name=registration.command.name, value=registration.command.doc, inline=False)
                else:
                    embed.add_field(name=registration.command.name, value='Command documentation unavailable', inline=False)
            embed.timestamp = datetime.now(tz=timezone.utc)

        await _message.channel.send(embed=embed)
