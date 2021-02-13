import subprocess
import discord

class Shell():
    def __init__(self, args):
        self.name = 'Shell'
        self.description = 'Allows shell access from Discord. This command is only available to the user defined in the config file.'
        self.syntax = ['shell *command*']
        self.args = args

    async def run(self):
        owner_id = self.configuration.getKeyValue('DEFAULT', 'owner_id')

        if int(self.message.author.id) != int(owner_id):
            return f'Permission Denied. {self.message.author.id} {owner_id}'

        process = subprocess.Popen(self.args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        stdout, stderr = process.communicate()
        if stdout and not stderr:
            return str(stdout.decode("utf-8"))
        elif not stdout and stderr:
            return str(stderr.decode("utf-8"))
        else:
            return f'{str(stdout.decode("utf-8"))}\n{str(stderr.decode("utf-8") )}'
