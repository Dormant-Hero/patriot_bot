import discord
from discord.ext import commands
from discord import app_commands
from icecream import ic
from config import OWNER_ID
from db import delete_row_db, existing_command_db, update_emb_command_db, fetch_all_commands_db, fetch_all_embed_commands_db, update_command_db, add_embed_command_db, add_command_db, in_other_table_db

RESERVED = {"help", "sync", "link"} 

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_commands()
        self.load_embed_commands()

# Cog listeners
    @commands.Cog.listener()
    async def on_ready(self):
        ic(f"logged in as {__name__} is online")

# Functions

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
        rows = fetch_all_commands_db()
        for name, description, response in rows: 
            self.create_command(name, description, response)

    def load_embed_commands(self):
        rows = fetch_all_embed_commands_db()
        for name, title, description, color, image_url, help_text in rows:
            self.create_embed_command(name, title, description, color, image_url, help_text)

    def command_name_handler(self, txt, embed=False):
        command_name = txt.lower()
        existing = existing_command_db(command_name, embed)
        if existing:
            action = "Updated"
        else:
            action = "Added"
        return command_name, existing, action

    def command_response_handler(self, response):
        if "\\n" in response:
            response = response.replace("\\n", "\n")
        return response

    async def cog_app_command_error(self, interaction, error):
        ic(error)
        msg = "Something went wrong. Check the logs."
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

# Commands

    @commands.command(name='sync', description='Owner only')
    async def sync(self, ctx):
        try:
            if ctx.author.id == OWNER_ID:
                await self.bot.tree.sync()
                await ctx.send("syncing commands boss")
            else:
                await ctx.send('You must be the owner of the bot to use this command!')
        except Exception as e:
            ic()
            ic(e)

# App commands (use the !sync command then restart the bot and your Discord client to see these commands in discord)

    @app_commands.command(name="link", description="Get a link to your character by typing the character name")
    @app_commands.describe(character_name='Please input your character name', )
    async def link(self, interaction: discord.Interaction, character_name: str):
        await interaction.response.send_message(
            f"Your character link should be <https://mgo2pc.com/profile/{character_name.replace(' ', '%20')}>")
        

    
                
    @app_commands.command(name="add_command", description="Add a ! command to the bot (e.g. !hello)")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(command_name='Please input the command name', command_description='Please input the command description', command_response='Please input the command response')
    async def add_command_to_bot(self, interaction: discord.Interaction, command_name: str, command_description: str, command_response: str):
        command_name_handle = self.command_name_handler(command_name)
        command_name = command_name_handle[0]
        already_embed_command = in_other_table_db(command_name)
        if command_name in RESERVED:
            await interaction.response.send_message("Cannot add a help command as this is already hard-coded.")
        elif not already_embed_command:
            command_existing = command_name_handle[1]
            db_action = command_name_handle[2]
            command_response = self.command_response_handler(command_response)
            if command_existing:
                update_command_db(command_name, command_response, command_description)
            else:
                add_command_db(command_name, command_description, command_response)
            self.bot.remove_command(command_name)
            self.create_command(command_name, command_description, command_response)
            await interaction.response.send_message(f"Command `{command_name}`, {db_action} successfully!")
        else:
            await interaction.response.send_message(f"Command `{command_name}` not created. `{command_name}` already exists as am embed command.")


    @app_commands.command(name="add_embed_command", description="Add a ! command to the bot (e.g. !hello) with an embed")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(emb_command_name="Please input the embed command name",
                            emb_title= "Please input the title of the embed post",
                            emb_command_description="Please input the embed command description", 
                            emb_command_content="This is the content which your embed will display",
                            emb_colour="Please input embed colour. This is an integer but you can leave this blank", # I will revisit this later to be a dropdown. Need to read the discord.py docs as it can be better.
                            image_url="Url of the image you would like the embed to contain")
    async def add_embed(self, interaction: discord.Interaction, emb_command_name: str, emb_title: str, emb_command_description: str,
                         emb_command_content: str, emb_colour: int = 3447003, image_url: str = None):
        command_name_handler = self.command_name_handler(emb_command_name, embed=True)
        emb_command_name = command_name_handler[0]
        already_non_embed_command = in_other_table_db(emb_command_name, embed=True)
        if emb_command_name in RESERVED:
            await interaction.response.send_message("Cannot add a help command as this is already hard-coded")
        elif not already_non_embed_command:
            emb_command_existing = command_name_handler[1]
            db_action = command_name_handler[2]
            emb_command_content = self.command_response_handler(emb_command_content)
            if emb_command_existing:
                update_emb_command_db(emb_command_name, emb_title, emb_command_description, emb_command_content, emb_colour, image_url)
            else:
                add_embed_command_db(emb_command_name, emb_title, emb_command_content, emb_colour, image_url, emb_command_description)
            self.bot.remove_command(emb_command_name)
            self.create_embed_command(
                name=emb_command_name,
                title=emb_title,
                description=emb_command_content,
                color=emb_colour,
                image_url=image_url,
                help_text=emb_command_description
            )
            await interaction.response.send_message(f"Embed command `{emb_command_name}` {db_action} successfully!")
        else:
            await interaction.response.send_message(f"Embed command `{emb_command_name}` not created. `{emb_command_name} already exists as a non-embed command.")

    @app_commands.command(name="delete_command")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(command_name="Please input the name of the embed or non-embed command you wish to delete.")
    async def delete_command(self, interaction: discord.Interaction, command_name: str):
        command_name = command_name.lower()
        exists_as_embed = existing_command_db(command_name, embed=True)
        exists_as_command = existing_command_db(command_name, embed=False)
        if exists_as_embed:
            self.bot.remove_command(command_name)
            delete_row_db(command_name, embed=True)
            await interaction.response.send_message(f"Embed command `{command_name}` deleted rejoice!")
        elif exists_as_command:
            self.bot.remove_command(command_name)
            delete_row_db(command_name, embed=False)
            await interaction.response.send_message(f"Command `{command_name}` deleted rejoice!")
        else:
            await interaction.response.send_message(f"Command `{command_name}` does not exist at all, thus not deleted. Do not rejoice")
        

async def setup(bot):
    await bot.add_cog(Commands(bot))
