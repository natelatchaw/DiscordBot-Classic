import platform
import discord

class Info():
    def __init__(self, args):
        self.name = 'Info'
        self.description = 'Returns info about the platform'
        self.syntax = ['Info']

    async def run(self):
        self.icon_url = 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/200px-Python-logo-notext.svg.png'

        embed = discord.Embed()
        embed.title = 'Platform Information'
        # embed.description = 'Underlying platform information'
        embed.add_field(name = '**System**', value = platform.system(), inline = False)
        embed.add_field(name = '**Node**', value = platform.node(), inline = False)
        embed.add_field(name = '**Release**', value = platform.release(), inline = False)
        embed.add_field(name = '**Version**', value = platform.version(), inline = False)
        embed.add_field(name = '**Machine**', value = platform.machine(), inline = False)
        embed.add_field(name = '**Processor**', value = platform.processor(), inline = False)
        embed.add_field(name = '**Platform**', value = platform.platform(), inline = False)
        embed.set_footer(text = "Python Version %s" % platform.python_version(), icon_url = self.icon_url)

        await self.message.channel.send(embed = embed)
