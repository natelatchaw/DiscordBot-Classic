class Echo():
    def __init__(self, args):
        self.name = 'Echo'
        self.args = args

    async def run(self):
        #print('<%s> command invoked by <%s>' % (self.name, self.message.author))
        string = ''
        for arg in self.args:
            string = '%s %s' % (string, arg)
        return string
