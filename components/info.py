import inspect
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import discord
from context import Context
from router.packaging import Component, Package


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

    async def help(self, context: Context, *, package: Optional[str] = None, component: Optional[str] = None):
        """
        Provides usage data for commands.

        Parameters:
            - package: specify a package to retrieve help data for
            - component: specify a component to retrieve help data for
        """

        no_doc: str = "No documentation provided."

        embed = discord.Embed()

        if package and not component:
            packages: List[Package] = self.__find_packages__(context, package=package)
            if len(packages) == 0:
                raise ValueError(f"No packages found matching '{package}'")
            if len(packages) > 1:
                raise ValueError(f"Multiple packages found matching'{package}'")
            selected_package: Package = packages[0]

            embed.title = selected_package._reference.name
            embed.description = inspect.cleandoc(selected_package.doc) if selected_package.doc else no_doc
            for selected_component in selected_package.values():
                embed.add_field(name=selected_component.name, value=selected_component.doc if selected_component.doc else no_doc, inline=False)
            embed.timestamp = datetime.now(tz=timezone.utc)
        
        elif component:
            components: List[Component] = self.__find_components__(context, component=component, package=package)
            if len(components) == 0:
                raise ValueError(f"No components found matching '{component}'")
            if len(components) > 1:
                raise ValueError(f"Multiple components found matching'{component}'")
            selected_component: Component = components[0]
            
            embed.title = selected_component.name
            embed.description = inspect.cleandoc(selected_component.doc) if selected_component.doc else no_doc
            for selected_command in selected_component.values():
                embed.add_field(name=selected_command.name, value=selected_command.doc if selected_command.doc else no_doc, inline=False)
            embed.timestamp = datetime.now(tz=timezone.utc)

        else:
            embed.title = "Help"
            embed.description = inspect.cleandoc(self.__doc__) if self.__doc__ else no_doc
            for selected_package in context.packages.values():
                embed.add_field(name=selected_package._reference.name, value=selected_package.doc if selected_package.doc else no_doc, inline=False)
            embed.timestamp = datetime.now(tz=timezone.utc)

        await context.message.channel.send(embed=embed)


    def __find_packages__(self, context: Context, *, package: str) -> List[Package]:
        """
        Returns a list of all packages matching the provided parameters.

        Raises:
            - KeyError: if no package matching the provided string exists
        """

        selected_package: Optional[Package] = context.packages.get(package)

        packages: List[Package] = [selected_package] if selected_package else list()

        return packages


    def __find_components__(self, context: Context, *, component: str, package: Optional[str] = None) -> List[Component]:
        """
        Returns a list of all components matching the provided parameters.

        Raises:
            - KeyError: if no package matching the provided string exists
        """
        
        selected_package: Optional[Package] = context.packages.get(package) if package else None

        packages: List[Package] = [selected_package] if selected_package else list(context.packages.values())

        components: List[Component] = [package.get(component) for package in packages if package.get(component) is not None]

        return components