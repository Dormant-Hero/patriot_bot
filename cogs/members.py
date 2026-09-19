import logging
import discord
from discord.ext import commands
from config import PATRIOTS_ROLE_ID

log = logging.getLogger(__name__)

class Members(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        role = member.guild.get_role(PATRIOTS_ROLE_ID)
        if role is None:
            log.error("Role %s not found in guild %s", PATRIOTS_ROLE_ID, member.guild.id)
            return

        try:
            await member.add_roles(role, atomic=True, reason="Auto-role on join")
        except discord.Forbidden:
            log.error("Missing permission or role hierarchy blocks assigning %s", role)
        else:
            log.info("Gave %s the %s role", member, role)

async def setup(bot):
    await bot.add_cog(Members(bot))
