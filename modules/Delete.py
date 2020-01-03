import discord

class Delete():
    def __init__(self, args):
        self.name = 'Delete'
        self.description = 'Deletes messages sent by the bot.'
        self.syntax = ['delete *user mention* *number of messages*']
        self.args = args

    async def run(self):
        output = self.console.output

        if not self.args:
            return 'I couldn\'t find a command argument. Did you specify how many messages I should delete?'

        message_number = self.parse_args(self.args)

        if not self.message.mentions:
            return f'It looks like you forgot to mention a user to delete messages from. Type **{self.prefix}help delete** for syntax information.'
        elif len(self.message.mentions) > 1:
            await self.message.channel.send(f'Multiple users mentioned. I\'ll use the first one: {self.message.mentions[0].mention}')
        if not message_number:
            return f'It looks like you forgot to add a number of messages to delete. Type **{self.prefix}help delete** for syntax information.'

        self.target_user = self.message.mentions[0]

        # get a list of messages from the text channel
        message_list = await self.message.channel.history().flatten()

        if len(message_list) == 0:
            return f'Could not pull message history from the text channel. This may be because there are no messages, or I may not have the necessary permissions to read message history.'

        total_messages = message_number
        for message in message_list:
            if self.message.id == message.id:
                output('Skipping deletion message')
            elif message.author == self.target_user and message_number != 0:
                output(f'Deleting message {message_number} of {total_messages}: {message.clean_content}')
                try:
                    await message.delete()
                    message_number = message_number - 1
                except discord.Forbidden as permissionError:
                    output('Deletion failed: missing permissions')
                    output(permissionError)
                    return 'I don\'t have the proper permissions to delete messages.'
                except discord.HTTPException as deletionError:
                    output('Deletion failed: HTTP Exception')
                    output(deletionError)
                    return f'Something went wrong. I couldn\'t delete this message:\n```{message.clean_content}```'

    def parse_args(self, args):
        output = self.console.output
        message_number = 0
        arg_number = 1
        for arg in args:
            try:
                message_number = int(arg)
                output(f'Found an integer in argument {arg_number}: {message_number} messages will be deleted')
            except ValueError as valueError:
                output(f'Parsed argument {arg_number} and didn\'t find an integer.')
            arg_number = arg_number + 1

        if message_number != 0:
            return message_number
        else:
            return None
