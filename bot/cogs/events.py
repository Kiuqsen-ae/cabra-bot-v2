import discord
from discord.ext import commands

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # tenta mandar mensagem no canal "geral" (se existir)
        channel = discord.utils.get(member.guild.text_channels, name="geral")
        if channel:
            await channel.send(f"Bem-vindo(a), {member.mention}! 🎉")

async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))