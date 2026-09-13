import discord
from aiohttp.hdrs import SERVER
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
from pathlib import Path
from icecream import ic

image_path = Path("event_image.png")

load_dotenv()

DEFAULT_ROLE = "Patriots"
# Connect to the agreSQL server.

kimi_id = 243555896884461568
dh_id = 699603124226228275

# testing enviornment_variables
db_name = os.environ.get("TEST_DBNAME")
bot_token = os.environ.get("TEST_TOKEN2")
patriots_role_id = 1277242036394917889
guild_id = 1277242036222824468
help_thread_id = 1277263982947995752
survival_channel_id = 1277242036701106213
adventure_kimi_thread_id = 1279170049374031986

# live variables
# db_name = os.environ.get("DBNAME")
# bot_token = os.environ.get("TOKEN")
# patriots_role_id = 809851420211150959
# guild_id = 809840002989162516
# help_thread_id = 1241119181466767501
# survival_channel_id = 1243287389657370664
# adventure_kimi_thread_id = 1281375345097965618


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
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


async def reload(cog):
    try:
        await cog
    except Exception as e:
        ic(e)
        await asyncio.sleep(60)
        await cog


async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await reload(bot.load_extension(f"cogs.{filename[:-3]}"))
            # await bot.load_extension(f"cogs.{filename[:-3]}")


async def main():
    async with bot:
        await load()
        await bot.start(bot_token)


asyncio.run(main())
