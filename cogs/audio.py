import asyncio
from typing import Any, Dict, Optional, List, Union

import disnake
from disnake.ext import tasks
import youtube_dl  # type: ignore
from disnake.ext import commands

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ""


YTDL_FORMAT_OPTIONS = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_delay_max 2 -reconnect_streamed 1',
    "options": "-vn -max_muxing_queue_size 2048 -dn -ignore_unknown -sn -fflags +discardcorrupt"
}

ytdl = youtube_dl.YoutubeDL(YTDL_FORMAT_OPTIONS)


class YTDLSource(disnake.PCMVolumeTransformer):
    def __init__(self, source: disnake.AudioSource, *, data: Dict[str, Any], volume: float = 0.5):
        super().__init__(source, volume)

        self.title = data.get("title")

    @classmethod
    async def from_url(
        cls, url, *, loop: Optional[asyncio.AbstractEventLoop] = None, stream: bool = False
    ):
        loop = loop or asyncio.get_event_loop()
        data: Any = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )

        if "entries" in data:
            # take first item from a playlist
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)

        return cls(
            disnake.FFmpegPCMAudio(filename, executable="C:/ffmpeg/bin/ffmpeg.exe", **FFMPEG_OPTIONS), data=data
        ), data


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.connected_client: Optional[disnake.VoiceClient] = None

    @commands.slash_command()
    async def dj(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @dj.sub_command()
    async def join(self, inter: disnake.ApplicationCommandInteraction):
        """
        Join the bot to the channel you're currently connected to.
        """

        # caller will ALWAYS be a member of the Discord, no DM support
        caller: disnake.Member = inter.author

        # channel that the person called from
        channel = caller.voice.channel

        if channel:
            bot_connection: List[Union[disnake.VoiceClient, disnake.VoiceProtocol]] = inter.bot.voice_clients

            # if there's an existing clients, move the bot
            if bot_connection:
                self.connected_client = inter.bot.voice_clients[0]
                await self.connected_client.move_to(channel)  # type: ignore
            else:
                # otherwise, connect to that channel
                self.connected_client = await channel.connect()

            await inter.response.send_message("🍧 I'm in your house, touching your things 🍧", ephemeral=True)

    # @dj.sub_command()
    # async def play(self, inter: disnake.ApplicationCommandInteraction, *, query: str):
    #     """Plays a file from the local filesystem"""
    #
    #     if not self.connected_client:
    #         await self.join(interaction=inter)
    #
    #     source = disnake.PCMVolumeTransformer(disnake.FFmpegPCMAudio(query, executable="C:/ffmpeg/bin/ffmpeg.exe"))
    #     self.connected_client.play(source, after=lambda e: print(f"Player error: {e}") if e else None)
    #
    #     await inter.response.send_message(f"🍧 Now playing {query}... 🍧", ephemeral=True)

    @tasks.loop(seconds=5.0)
    async def check_player_status(self):
        """
        Set up a task loop to check our player status, and if it's not playing anything, disconnect it.
        """
        if not self.connected_client.is_playing():
            await self.connected_client.disconnect()

            # noticed some odd behaviour when repeatedly connecting and reconnecting, this might be unnecessary
            self.connected_client = None

            # cancel the task
            self.check_player_status.cancel()

    @dj.sub_command()
    async def play(self, inter: disnake.ApplicationCommandInteraction, *, url: str):
        """Plays a file from a provided YouTube URL"""

        if not self.connected_client or self.connected_client.is_connected():
            await self.join(interaction=inter)

        source, data = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
        self.connected_client.play(source, after=lambda e: print(f"Player error: {e}") if e else None)

        # start our listener loop
        self.check_player_status.start()

        # if we've already responded to the message because they weren't in the channel:
        if inter.response.is_done():
            await inter.edit_original_response(
                content=f"🍧 Now playing {source.title}... 🍧",
            )
        else:
            await inter.response.send_message(f"🍧 Now playing {source.title}... 🍧", ephemeral=True)

    @dj.sub_command()
    async def stop(self, inter: disnake.ApplicationCommandInteraction):
        """
        Stops whatever the bot is currently playing.
        """

        # if we're actually playing something, kill it and remove our client
        if self.connected_client.is_playing():

            # kill the connected client and nuke it from scope
            await self.connected_client.disconnect()
            self.connected_client = None

            # cancel our looped task to check if it's still playing
            self.check_player_status.cancel()
            await inter.response.send_message(f"🍧 The deed is done. 🍧", ephemeral=True)

        # we're not currently doing anything, and the task should insult the user
        else:
            await inter.response.send_message(f"🍧 I ain't doing anything, ya' clown. 🍧", ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))
