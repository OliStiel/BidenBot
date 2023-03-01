import os

from dotenv import load_dotenv

from disnake import Intents
from disnake.ext.commands import InteractionBot


# my discord dev server ID
TEST_GUILD_ID = 1080618917925486622


def setup_bot():
    """
    Setup function where we're going to be putting in all the bits and pieces that get loaded into the bot.

    :return: The bot with everything setup
    """

    # retrieve our environment variables
    load_dotenv()

    # set what the bot is capable of retrieving
    intents = Intents(messages=True, guilds=True, message_content=True)

    # we're using an InteractionBot here because we're not going to support prefixing
    bot = InteractionBot(intents=intents, test_guilds=[TEST_GUILD_ID])

    # load our extended functionality using the cogs method
    bot.load_extension('cogs.basics')

    # add all of our events
    @bot.event
    async def on_ready():
        print("DIAMOND JOE RISES AGAIN")

    return bot


def main():
    # pull in all of our extensions and such
    bot = setup_bot()

    # run the BidenBot client
    bot.run(os.environ['BOT_TOKEN'])


if __name__ == "__main__":
    main()
