class Hello():
    def __init__(self, args):
        self.name = 'Hello'
        self.description = 'Posts \'hello world\' to the channel'
        self.syntax = ['hello']

    async def run(self):
        print('<%s> command invoked by <%s>' % (self.name, self.message.author))
        return 'hello world'
