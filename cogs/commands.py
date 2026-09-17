import discord
import asyncio
from discord.ext import commands
from discord import app_commands
# note the below is pip install python-dotenv to get this one installed!
from dotenv import load_dotenv
import os
from icecream import ic
import time
from pathlib import Path
import psycopg
import sys
import typing
import threading

load_dotenv()

DH_ID = int(os.environ.get("DH_ID")) 
# testing enviornment_variables
DB_NAME = os.environ.get("TEST_DBNAME")
PATRIOTS_ROLE_ID = os.environ.get("PATRIOT_ROLE_ID")
DB_USER = os.environ.get("USERNME")
DB_PASSWORD = os.environ.get("PASSWORD")
DB_HOST = os.environ.get("HOST")
DB_PORT = os.environ.get("PORT")
DB_CONNNECTION_STRING = f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host={DB_HOST} port={DB_PORT}"

# live variables
# DB_NAME = os.environ.get("DBNAME")
# PATRIOTS_ROLE_ID = os.environ.get("PATRIOT_ROLE_ID")

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_commands()
        self.load_embed_commands()

    @commands.Cog.listener()
    async def on_ready(self):
        ic(f"logged in as {__name__} is online")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role = member.guild.get_role(PATRIOTS_ROLE_ID)
        await member.add_roles(role, atomic=True)
        ic(f"{member} was given {role} role")

    # Function to create a command
    def create_command(self, name, description, response):
        async def command(ctx):
            await ctx.send(response)

        command.__name__ = name
        self.bot.command(name=name, help=description)(command)

    # Function to create an embed command
    def create_embed_command(self, name, title, description, color, image_url=None, help_text=None):
        async def command(ctx):
            embed = discord.Embed(title=title, description=description, color=color)
            if image_url:
                embed.set_image(url=image_url)
            await ctx.send(embed=embed)

        command.__name__ = name
        self.bot.command(name=name, help=help_text)(command)

    def load_commands(self):
        with psycopg.connect(DB_CONNNECTION_STRING) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT command_name, command_description, command_response FROM bot_commands")
                rows = cur.fetchall()
        for name, description, response in rows: # for loop outside of connection as to not interrupt it.
            self.create_command(name, description, response)
        # conn.close() no longer needed in psycopg3, the context manager handles closing the connection automatically.
        # No need for the connection pool as this is just one load of commands at startup and the connection is closed after that. Cold boot is fine as just miliseconds.

    
    def load_embed_commands(self):
        with psycopg.connect(DB_CONNNECTION_STRING) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT command_name, command_title, command_description, embed_color, embed_image, embed_help FROM bot_commands_embed")
                rows = cur.fetchall()
        for name, title, description, color, image_url, help_text in rows: # for loop outside of connection as to not interrupt it.
            self.create_embed_command(name, title, description, color, image_url, help_text)

    @commands.command(name='sync', description='Owner only')
    async def sync(self, ctx):
        try:
            if ctx.author.id == DH_ID:
                await self.bot.tree.sync()
                await ctx.send("syncing commands boss")
            else:
                await ctx.send('You must be the owner of the bot to use this command!')
        except Exception as e:
            ic()
            ic(e)

    @app_commands.command(name="link", description="Get a link to your character by typing the character name")
    @app_commands.describe(character_name='Please input your character name', )
    async def link(self, interaction: discord.Interaction, character_name: str):
        await interaction.response.send_message(
            f"Your character link should be <https://mgo2pc.com/profile/{character_name.replace(' ', '%20')}>")
        
async def setup(bot):
    await bot.add_cog(Commands(bot))
