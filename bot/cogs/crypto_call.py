import aiohttp
import discord

from discord.ext import commands, tasks

# =========================================
# ORDEM DOS CANAIS = ORDEM DESTA LISTA
# tipo:
# - "fiat_usd_brl" -> usa tether em BRL
# - "fiat_eur_brl" -> usa exchange_rates
# - "crypto"       -> usa simple/price em USD
# =========================================
CANAIS = [
    ("USD/BRL", "tether", "fiat_usd_brl"),
    ("EUR/BRL", "eur", "fiat_eur_brl"),

    ("BTC", "bitcoin", "crypto"),
    ("ETH", "ethereum", "crypto"),
    ("JUP", "jupiter-exchange-solana", "crypto"),
    ("XRP", "ripple", "crypto"),
    ("SOL", "solana", "crypto"),
    ("RON", "ronin", "crypto"),
    ("BNB", "binancecoin", "crypto"),
]

CATEGORIA = "Crypto Preço"


class CryptoCall(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channels = {}
        self.last_prices = {}
        self.initialized_guilds = set()

    async def cog_load(self):
        self.update_prices.start()

    async def cog_unload(self):
        self.update_prices.cancel()

    async def fetch_simple_prices(
        self,
        session: aiohttp.ClientSession,
        coin_ids: list[str]
    ) -> dict:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": "usd,brl",
        }

        try:
            async with session.get(url, params=params, timeout=15) as resp:
                if resp.status != 200:
                    print(f"Erro CoinGecko /simple/price: status {resp.status}")
                    return {}

                data = await resp.json()
                return data if isinstance(data, dict) else {}
        except Exception as e:
            print(f"Erro ao buscar simple price: {e}")
            return {}

    async def fetch_eur_brl(self, session: aiohttp.ClientSession) -> float | None:
        url = "https://api.coingecko.com/api/v3/exchange_rates"

        try:
            async with session.get(url, timeout=15) as resp:
                if resp.status != 200:
                    print(f"Erro CoinGecko /exchange_rates: status {resp.status}")
                    return None

                data = await resp.json()

                rates = data.get("rates", {})
                eur = rates.get("eur", {}).get("value")
                brl = rates.get("brl", {}).get("value")

                if eur is None or brl is None:
                    return None

                # exchange_rates é baseado em BTC
                # então EUR/BRL = brl / eur
                return float(brl) / float(eur)
        except Exception as e:
            print(f"Erro ao buscar EUR/BRL: {e}")
            return None

    async def reset_channels_for_guild(self, guild: discord.Guild):
        category = discord.utils.get(guild.categories, name=CATEGORIA)

        if category is None:
            category = await guild.create_category(CATEGORIA)

        for vc in list(category.voice_channels):
            try:
                await vc.delete()
            except Exception as e:
                print(f"Erro ao deletar canal {vc.name}: {e}")

        for nome, _coin_id, _tipo in CANAIS:
            try:
                canal = await guild.create_voice_channel(
                    name=f"{nome} carregando...",
                    category=category
                )
                self.channels[(guild.id, nome)] = canal
            except Exception as e:
                print(f"Erro ao criar canal {nome}: {e}")

        self.initialized_guilds.add(guild.id)

    def format_usd(self, price: float) -> str:
        if price >= 1000:
            return f"{price:,.2f}"
        elif price >= 1:
            return f"{price:.2f}"
        else:
            return f"{price:.4f}"

    def format_brl(self, price: float) -> str:
        return f"{price:.2f}"

    @tasks.loop(minutes=10)
    async def update_prices(self):
        async with aiohttp.ClientSession() as session:
            simple_ids = [
                coin_id
                for _nome, coin_id, tipo in CANAIS
                if tipo in ("fiat_usd_brl", "crypto")
            ]

            simple_data = await self.fetch_simple_prices(session, simple_ids)
            eur_brl = await self.fetch_eur_brl(session)

            for guild in self.bot.guilds:
                if guild.id not in self.initialized_guilds:
                    await self.reset_channels_for_guild(guild)

                for nome, coin_id, tipo in CANAIS:
                    canal = self.channels.get((guild.id, nome))
                    if canal is None:
                        continue

                    if tipo == "fiat_usd_brl":
                        tether_data = simple_data.get(coin_id, {})
                        brl_price = tether_data.get("brl")

                        if brl_price is None:
                            novo_nome = f"⚪ {nome} erro"
                        else:
                            novo_nome = f"💵 {nome} R${self.format_brl(float(brl_price))}"

                    elif tipo == "fiat_eur_brl":
                        if eur_brl is None:
                            novo_nome = f"⚪ {nome} erro"
                        else:
                            novo_nome = f"💶 {nome} R${self.format_brl(eur_brl)}"

                    else:
                        coin_data = simple_data.get(coin_id, {})
                        usd_price = coin_data.get("usd")

                        if usd_price is None:
                            novo_nome = f"⚪ {nome} erro"
                        else:
                            usd_price = float(usd_price)
                            last = self.last_prices.get((guild.id, nome))
                            emoji = "⚪"

                            if last is not None:
                                if usd_price > last:
                                    emoji = "🟢"
                                elif usd_price < last:
                                    emoji = "🔴"

                            self.last_prices[(guild.id, nome)] = usd_price
                            novo_nome = f"{emoji} {nome} ${self.format_usd(usd_price)}"

                    if canal.name != novo_nome:
                        try:
                            await canal.edit(name=novo_nome)
                        except Exception as e:
                            print(f"Erro ao renomear {nome}: {e}")

    @update_prices.before_loop
    async def before_update_prices(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(CryptoCall(bot))