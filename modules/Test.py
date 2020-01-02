class Test():
    def __init__(self, args):
        self.name = 'Test'
        self.description = 'Checks if bot is operational'
        self.syntax = ['test']

    async def run(self):
        print(f'{self.name} command invoked by {self.message.author}')
        return 'Bot is online'
