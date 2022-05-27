from datetime import datetime, time, timedelta, timezone
import os
from typing import Dict, List, Optional
import discord
from router.packaging import Package, Component

from context import Context

class Info:
    """
    Provides information about the client.
    """

    def __init__(self, *args, **kwargs):
        pass

    async def about(self, context: Context):
        """
        Provides metadata about the current instance.
        """

        embed = discord.Embed()
        embed.title = 'About'

        uptime: timedelta = datetime.now(tz=timezone.utc) - context.timestamp
        embed.add_field(name='Current Uptime', value=str(uptime))

        package_names: List[str] = [package._reference.name for package in context.packages.values()]
        embed.add_field(name='Loaded Packages', value='\n'.join(package_names), inline=False)

        embed.add_field(name='Shard ID', value=context.client.shard_id, inline=False)
        embed.add_field(name='Total Shards', value=context.client.shard_count, inline=False)
        embed.add_field(name='Available Cores', value=os.cpu_count(), inline=False)

        embed.timestamp = context.timestamp

        await context.message.channel.send(embed=embed)

    async def help(self, context: Context, *, package: str = None, component: str = None):
        """
        Provides usage data for commands.

        Parameters:
            -component: specify a component to retrieve help data for
        """

        embed = discord.Embed()

        if package:
            try:
                selected_package: Package = context.packages[package]
            except KeyError:
                await context.message.channel.send(f'Could not find a package named **{package}**')
                return

            embed.title = selected_package._reference.name
            embed.description = selected_package.doc
            for component in selected_package.values():
                embed.add_field(name=component.name, value=component.doc, inline=False)
            embed.timestamp = datetime.now(tz=timezone.utc)
        
        elif component:
            selected_component: Optional[Component] = None
            for p in context.packages.values():
                try:
                    selected_component = p[component]
                except KeyError:
                    continue
            if not selected_component:
                await context.message.channel.send(f'Could not find a component named **{component}**')
                return
            
            embed.title = selected_component.name
            embed.description = selected_component.doc
            for command in selected_component.values():
                embed.add_field(name=command.name, value=command.doc, inline=False)
            embed.timestamp = datetime.now(tz=timezone.utc)

        else:
            embed.title = "Help"
            embed.description = self.__doc__
            for package in context.packages.values():
                embed.add_field(name=package._reference.name, value=package.doc, inline=False)
            embed.timestamp = datetime.now(tz=timezone.utc)

        await context.message.channel.send(embed=embed)
