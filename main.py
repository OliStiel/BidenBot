import os

from dotenv import load_dotenv

import disnake
from disnake.ext.commands import Bot


# discord dev server IDs
TEST_GUILD_IDS = [1080618917925486622, 484807069111943171, 618158757574344724]


def setup_bot():
    """
    Setup function where we're going to be putting in all the bits and pieces that get loaded into the bot.

    :return: The bot with everything setup
    """

    # retrieve our environment variables
    load_dotenv()

    # set what the bot is capable of retrieving
    intents = disnake.Intents.default()
    intents.presences = True
    intents.members = True
    intents.message_content = True

    # we're using an InteractionBot here because we're not going to support prefixing
    bot = Bot(intents=intents, test_guilds=TEST_GUILD_IDS, command_prefix="$")

    # add all of our events
    @bot.event
    async def on_ready():
        print("DIAMOND JOE RISES AGAIN")

    # load our basic functionality, currently nothing
    # bot.load_extension('cogs.basics')

    # load our audio functionality
    bot.load_extension('cogs.audio')

    return bot


def main():
    # pull in all of our extensions and such
    bot = setup_bot()

    # run the BidenBot client
    bot.run(os.environ['BOT_TOKEN'])


if __name__ == "__main__":
    main()
