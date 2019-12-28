class Help():
    def __init__(self, args):
        from os import listdir
        import os

        self.name = 'Help'
        self.args = args

    async def run(self):
        #print('<%s> command invoked by <%s>' % (self.name, self.message.author))
        string = ''

        commands = {}
        directory_contents = os.listdir(os.path.getcwd() + '/modules')
        for item in directory_contents:
            filename = os.path.basename(item)
            if os.path.splittext(filename)[-1] is '.py':
                commands.append(os.path.splittext(filename)[0])
            command_list'\n'.join(commands)


        for arg in self.args:
            # string = '%s %s' % (string, arg)
        return commands
