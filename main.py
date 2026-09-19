import discord
from discord.ext import commands
import asyncio
import logging
from pathlib import Path
from icecream import ic
from config import TOKEN

logging.basicConfig(level=logging.INFO)

COGS_DIR = Path(__file__).parent / "cogs"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True, status=discord.Status.online)
bot.remove_command("help")


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    activity = discord.Activity(
        name="Metal Gear Online 2",
        type=discord.ActivityType.playing,
        # below not supported for bots but in case one day it is
        assets={
            "large_image": "large-image",  # The key for the large image asset you uploaded in the Developer Portal
            "large_text": "Metal Gear Online 2"  # Tooltip for the large image
        }
    )
    await bot.change_presence(activity=activity)


async def load_cog(name):
    try:
        await bot.load_extension(name)
    except Exception as e:
        ic(e)
        await asyncio.sleep(60)
        await bot.load_extension(name)


async def load():
    for path in COGS_DIR.glob("*.py"):
        await load_cog(f"cogs.{path.stem}")


async def main():
    async with bot:
        await load()
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())