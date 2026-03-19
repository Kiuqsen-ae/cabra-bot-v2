import discord
from discord.ext import commands
from discord import app_commands

class ComandsCrypto(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="crypto", description="Exemplo")
    async def crypto(self, interaction: discord.Interaction):
        await interaction.response.send_message("Cog crypto funcionando!")

async def setup(bot: commands.Bot):
    await bot.add_cog(ComandsCrypto(bot))