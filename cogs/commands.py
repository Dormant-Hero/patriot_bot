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
import psycopg2  # sudo yum install libpq-devel for fedora host
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
import typing
import threading

load_dotenv()

DH_ID = int(os.environ.get("DH_ID")) 
# testing enviornment_variables
DB_NAME = os.environ.get("TEST_DBNAME")
PATRIOTS_ROLE_ID = os.environ.get("PATRIOT_ROLE_ID")

# live variables
# DB_NAME = os.environ.get("DBNAME")
# PATRIOTS_ROLE_ID = os.environ.get("PATRIOT_ROLE_ID")

def open_db_connection():
    connection = psycopg2.connect(
        dbname=DB_NAME,
        user=os.environ.get("USERNME"),
        password=os.environ.get("PASSWORD"),
        host=os.environ.get("HOST"),
        port=os.environ.get("PORT"),
        connect_timeout=5,
        keepalives=1,
        keepalives_idle=45,
        keepalives_interval=10,
        keepalives_count=3,
        application_name="patriot_bot",
        options="-c statement_timeout=5000"
    )
    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return connection


class ReconnectingCursor:
    def __init__(self):
        self._connection = None
        self._cursor = None
        self._lock = threading.Lock()
        self._last_query = None
        self._last_params = None

    @staticmethod
    def _is_reconnectable_error(error):
        return isinstance(error, (psycopg2.InterfaceError, psycopg2.OperationalError))

    @staticmethod
    def _is_read_query(query):
        normalized = str(query).lstrip().lstrip("(").lower()
        return normalized.startswith(("select", "show", "table"))

    def _close(self):
        if self._cursor is not None:
            try:
                self._cursor.close()
            except Exception:
                pass
        if self._connection is not None:
            try:
                self._connection.close()
            except Exception:
                pass
        self._cursor = None
        self._connection = None

    def _open(self):
        self._close()
        self._connection = open_db_connection()
        self._cursor = self._connection.cursor()

    def _ensure_open(self):
        if (
            self._connection is None
            or self._connection.closed
            or self._cursor is None
            or self._cursor.closed
        ):
            self._open()

    def _recover_for_new_operation(self, error):
        self._close()
        if not self._is_reconnectable_error(error):
            raise error

    def _retry_last_read(self, error):
        if not self._is_reconnectable_error(error):
            raise error
        if not self._last_query or not self._is_read_query(self._last_query):
            raise error

        self._open()
        self._cursor.execute(self._last_query, self._last_params)

    def execute(self, query, params=None):
        self._last_query = query
        self._last_params = params

        with self._lock:
            try:
                self._ensure_open()
                self._cursor.execute(query, params)
            except Exception as error:
                self._recover_for_new_operation(error)
                if not self._is_read_query(query):
                    raise

                self._open()
                self._cursor.execute(query, params)

    def fetchone(self):
        with self._lock:
            try:
                return self._cursor.fetchone()
            except Exception as error:
                self._recover_for_new_operation(error)
                self._retry_last_read(error)
                return self._cursor.fetchone()

    def fetchall(self):
        with self._lock:
            try:
                return self._cursor.fetchall()
            except Exception as error:
                self._recover_for_new_operation(error)
                self._retry_last_read(error)
                return self._cursor.fetchall()

    @property
    def connection(self):
        return self._connection

    def __getattr__(self, name):
        return getattr(self._cursor, name)


db_cursor = ReconnectingCursor()
cur = db_cursor


async def database_health_check_loop():
    await asyncio.sleep(10)
    while True:
        try:
            cur.execute("SELECT 1")
            cur.fetchone()
        except Exception as error:
            ic("Database health check failed:", error)
        await asyncio.sleep(60)

def restart_bot():
    os.execv(sys.executable, [sys.executable] + sys.argv)

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_health_task = None
        self.load_commands()
        # Load embeds initially
        self.load_embeds()

    async def restart_cog(self):
        try:
            # Unload and reload the current cog
            ic("Restarting the cog...")
            extension_name = 'cogs.commands'  # Replace with the actual name of your cog module
            await self.bot.reload_extension(extension_name)
            ic(f"{extension_name} Cog has been restarted successfully!")
        except Exception as e:
            ic(f"Failed to restart the cog: {str(e)}")

    @commands.Cog.listener()
    async def on_ready(self):
        ic()
        ic(f"logged in as {__name__} is online")

        if self.db_health_task is None or self.db_health_task.done():
            self.db_health_task = asyncio.create_task(database_health_check_loop())

    def cog_unload(self):
        if self.db_health_task is not None:
            self.db_health_task.cancel()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role = member.guild.get_role(PATRIOTS_ROLE_ID)
        await member.add_roles(role, atomic=True)
        ic(f"{member} was given {role} role")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

    # Function to create a command
    def create_command(self, name, description, response):
        async def command(ctx):
            await ctx.send(response)

        command.__name__ = name
        self.bot.command(name=name, help=description)(command)

    # Function to load commands from the JSON file
    def load_commands(self):
        cur.execute(f"SELECT * FROM bot_commands")
        rows = cur.fetchall()
        for row in rows:
            command_name = row[1]
            command_desc = row[2]
            command_response = row[3]
            self.create_command(command_name, command_desc, command_response)


    # Load commands initially

    # Function to create a command for sending an embed
    def create_embed_command(self, name, title, description, color, image_url=None, help_text=None):
        async def command(ctx):
            ic(name, title, description, color, image_url, help_text)
            embed = discord.Embed(title=title, description=description, color=color)
            if image_url:
                embed.set_image(url=image_url)
            await ctx.send(embed=embed)

        command.__name__ = name
        self.bot.command(name=name, help=help_text)(command)

    def load_embeds(self):
        cur.execute(f"SELECT * FROM bot_commands_embed")
        rows = cur.fetchall()
        for row in rows:
            embed_name = row[1]
            embed_title = row[2]
            embed_content = row[3]
            embed_colour = row[4]
            embed_image = row[5]
            embed_help_desc = row[6]
            self.create_embed_command(embed_name, embed_title, embed_content, embed_colour, embed_image,
                                      embed_help_desc)




    # Command to add a new command
    @app_commands.command(name="add_command")
    @app_commands.describe(command_name="Add a new !command name",
                           command_description="Describe what the command does",
                           command_response="Paste the message the command will respond with"
                           )
    async def add_command_to_bot(self, interaction: discord.Interaction, command_name: str, command_description: str,
                                 command_response: str):
        if "\\n" in command_response:
            command_response = command_response.replace("\\n", "\n")
        command_name = command_name.lower()

        cur.execute(
            "SELECT id FROM bot_commands WHERE lower(command_name) = lower(%s)",
            (command_name,)
        )
        existing = cur.fetchone()
        action = "updated" if existing else "added"

        if existing:
            cur.execute(
                """
                UPDATE bot_commands
                SET command_response = %s
                WHERE lower(command_name) = lower(%s)
                """,
                (command_response, command_name)
            )
        else:
            cur.execute(
                """
                INSERT INTO bot_commands
                    (command_name, command_description, command_response)
                VALUES (%s, %s, %s)
                """,
                (command_name, command_description, command_response)
            )

        self.bot.remove_command(command_name)
        self.create_command(command_name, command_description, command_response)

        await interaction.response.send_message(
            f'Command `{command_name}` {action} successfully!'
        )

    # Command to add a new command
    @app_commands.command(name="delete_command")
    @app_commands.describe(command_name="Type !command that needs deleting")
    async def delete_bot_command(self, interaction: discord.Interaction, command_name: str):
        command_already_exists = False
        cur.execute(f"SELECT * FROM bot_commands")
        rows = cur.fetchall()
        for row in rows:
            if command_name.lower() == row[1].lower():
                command_already_exists = True
        if command_already_exists:
            cur.execute(f"DELETE FROM bot_commands WHERE command_name = '{command_name.lower()}'")
            await interaction.response.send_message(f'Command `{command_name.lower()}` deleted successfully!')
            await self.restart_cog()
        else:
            await interaction.response.send_message(f'Command `{command_name.lower()}` does not exist!')

    @app_commands.command(name="delete_embed")
    @app_commands.describe(command_name="Type embed !command that needs deleting")
    async def delete_embed(self, interaction: discord.Interaction, command_name: str):
        command_already_exists = False
        cur.execute(f"SELECT * FROM bot_commands_embed")
        rows = cur.fetchall()
        for row in rows:
            if command_name.lower() == row[1].lower():
                command_already_exists = True
        if command_already_exists:
            cur.execute(f"DELETE FROM bot_commands_embed WHERE command_name = '{command_name.lower()}'")
            await interaction.response.send_message(f'Embed command `{command_name.lower()}` deleted successfully!')
            await self.restart_cog()
        else:
            await interaction.response.send_message(f'Embed command `{command_name.lower()}` does not exist!')

    # Command to add a new embed
    @app_commands.command(name="add_embed_command")
    @app_commands.describe(emb_com_name='Name of embed !command',
                           emb_com_content='What you want in the body of the embed',
                           emb_title="Title of the embed itself",
                           emb_com_help_description="Description of what your command will do",
                           colour="This is an integer but you can leave it blank",
                           image_url="Url of the image you would like to add")
    async def add_embed(self, interaction: discord.Interaction, emb_com_name: str, emb_com_content: str,
                        emb_title: str, emb_com_help_description: str, colour: int = None, image_url: str = None):
        if colour is None:
            colour = 3447003
        if "\\n" in emb_com_content:
            emb_com_content = emb_com_content.replace("\\n", "\n")
        emb_com_name = emb_com_name.lower()

        cur.execute(
            "SELECT id FROM bot_commands_embed WHERE lower(command_name) = lower(%s)",
            (emb_com_name,)
        )
        existing = cur.fetchone()
        action = "updated" if existing else "added"

        if existing:
            cur.execute(
                """
                UPDATE bot_commands_embed
                SET command_title = %s,
                    command_description = %s,
                    embed_color = %s,
                    embed_image = %s,
                    embed_help = %s
                WHERE lower(command_name) = lower(%s)
                """,
                (emb_title, emb_com_content, colour, image_url, emb_com_help_description, emb_com_name)
            )
        else:
            cur.execute(
                """
                INSERT INTO bot_commands_embed
                    (command_name, command_title, command_description,
                     embed_color, embed_image, embed_help)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (emb_com_name, emb_title, emb_com_content, colour, image_url,
                 emb_com_help_description)
            )

        self.bot.remove_command(emb_com_name)
        self.create_embed_command(
            name=emb_com_name,
            title=emb_title,
            description=emb_com_content,
            color=colour,
            image_url=image_url,
            help_text=emb_com_help_description
        )

        await interaction.response.send_message(
            f'Embed command `{emb_com_name}` {action} successfully!'
        )

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
