class Test():
    def __init__(self, args):
        self.name = 'Test'
        self.description = 'Checks if bot is operational'
        self.syntax = ['test']

    async def run(self):
        print('<%s> command invoked by <%s>' % (self.name, self.message.author))
        return 'Bot is online'
