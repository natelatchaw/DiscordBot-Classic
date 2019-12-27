import os
import xml.etree.cElementTree as ET

class MessageLogger():
    def __init__(self):
        self.cwd = os.getcwd()
        self.usersFolder = ''
        self.xmlFile = ''

    async def run(self):
        messageData = dict(author = self.message.author, content = self.message.clean_content, id = self.message.id)
        self.message.created_at
