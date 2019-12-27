import os
import configparser

class Prefix():
    def __init__(self, args):
        self.name = 'Prefix'
        self.args = args

    async def run(self):
        print('<%s> command invoked by <%s>' % (self.name, self.message.author))

        if len(self.args) == 0:
            return 'no arguments provided'

        self.config = configparser.ConfigParser()
        self.file = os.path.abspath('./config.ini')
        self.config.read(self.file)
        self.config['DEFAULT']['prefix'] = str(self.args[0])
        with open(self.file, 'w') as configFile:
            self.config.write(configFile)

        return "prefix set to: `%s`" % self.args[0]
