import discord
from discord import app_commands
from discord.ext import commands

class Basic(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Mostra a latência do bot")
    async def ping(self, interaction: discord.Interaction):
        ms = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong! 🏓 {ms}ms")

    @app_commands.command(name="ajuda", description="Lista comandos do bot")
    async def ajuda(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Comandos:\n"
            "- /ping: mostra latência\n"
            "- /ajuda: mostra esta mensagem"
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Basic(bot))