import discord
from router.command import Command

class Help:
    """
    Provides information on available modules.
    """

    def __init__(self):
        pass

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
                embed.timestamp = _message.created_at
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
            embed.timestamp = _message.created_at

        await _message.channel.send(embed=embed)