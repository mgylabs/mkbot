# Test MK Bot Extension
async def hello(ctx):
    await ctx.send('Hello {0.display_name}.'.format(ctx.author))


def setup(bot):
    bot.add_command(bot.MGCert.bind(hello, 1))


def teardown(bot):
    print('I am being unloaded!')
