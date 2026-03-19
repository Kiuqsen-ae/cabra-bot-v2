import os
import discord
from discord.ext import commands
from bot.config import TOKEN

INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True  # necessário para eventos de membro entrar

class MyBot(commands.Bot):
    async def setup_hook(self):
        # carrega cogs automaticamente
        for arquivo in os.listdir("./bot/cogs"):
            if arquivo.endswith(".py") and arquivo != "__init__.py":
                nome_cog = arquivo[:-3]
                try:
                    await self.load_extension(f"bot.cogs.{nome_cog}")
                    print(f"✅ Cog carregado: {nome_cog}")
                except Exception as e:
                    print(f"❌ Erro ao carregar cog {nome_cog}: {e}")

        # sincroniza slash commands
        await self.tree.sync()

bot = MyBot(command_prefix="!", intents=INTENTS)

@bot.event
async def on_ready():
    print(f"✅ Mene, Mene, Tekel, Upharsin (id: {bot.user.id})")



bot.run(TOKEN)