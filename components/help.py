import discord
from router.command import CommandInterface

class Help:
    """
    Provides information on available modules.
    """

    def __init__(self):
        pass

    async def help(self, *, _message: str, _modules: dict, module: str=None):
        """
        Provides usage data for commands.

        Parameters:
            -module: specify a module to retrieve help data for
        """
        embed = discord.Embed()
        if module:
            try:
                targetModule = _modules[module]
                embed.title = targetModule.name
                embed.description = targetModule.doc
                for command in targetModule.commands.items():
                    command_name: str = command[0]
                    command: CommandInterface = command[1]
                    if command.doc:
                        embed.add_field(name=command_name, value=command.doc, inline=False)
                    else:
                        embed.add_field(name=command_name, value='Command documentation unavailable', inline=False)
                embed.timestamp = _message.created_at
            except KeyError:
                await _message.channel.send(f'Could not find a module named **{module}**')
                return

        else:
            embed.title = "Help"
            embed.description = self.__doc__
            for name, module in _modules.items():
                if module.doc:
                    embed.add_field(name=module.name, value=module.doc, inline=False)
                else:
                    embed.add_field(name=module.name, value='Module documentation unavailable', inline=False)
            embed.timestamp = _message.created_at

        await _message.channel.send(embed=embed)
