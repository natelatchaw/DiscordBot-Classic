import os
import configparser

class Prefix():
    def __init__(self, args):
        self.name = 'Prefix'
        self.description = 'Changes the bot\'s prefix'
        self.syntax = ['prefix *new prefix*']

    async def run(self):
        print(f'{self.name} command invoked by {self.message.author}')

        if len(self.args) == 0:
            return 'no arguments provided'

        self.config = configparser.ConfigParser()
        self.file = os.path.abspath('./config.ini')
        self.config.read(self.file)
        self.config['DEFAULT']['prefix'] = str(self.args[0])
        with open(self.file, 'w') as configFile:
            self.config.write(configFile)

        return f'prefix set to: {self.args[0]}'
