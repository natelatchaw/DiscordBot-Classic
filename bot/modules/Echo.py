class Echo():
    def __init__(self, args):
        self.name = 'Echo'
        self.args = args
        self.description = 'Echoes text entered by the user following the echo command'
        self.syntax = ['echo *text to be echoed*']

    async def run(self):
        #print('<%s> command invoked by <%s>' % (self.name, self.message.author))
        string = ''
        for arg in self.args:
            string = f'{string} {arg}'
        return string
