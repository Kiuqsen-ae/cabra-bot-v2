import os
import io
import asyncio
import requests
import discord
from discord.ext import commands
from dotenv import load_dotenv

# ✅ ZXing
import zxingcpp
from PIL import Image

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

CANAL_QR_ID = 1461658108081209406  # seu canal
DELETE_AFTER = 60  # segundos

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


def decode_qr_zxing(image_bytes: bytes) -> list[str]:
    """
    Decodifica QR Codes usando ZXing (bem mais forte que OpenCV/pyzbar).
    Retorna lista de textos decodificados (pode haver mais de 1 QR).
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    results = zxingcpp.read_barcodes(img)

    decoded = []
    for r in results:
        if r.text:
            decoded.append(r.text)

    # remove duplicados mantendo ordem
    seen = set()
    uniq = []
    for t in decoded:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user} (discord.py {discord.__version__})")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Só aceita nesse canal
    if message.channel.id != CANAL_QR_ID:
        return

    # Precisa ter imagem anexada
    if not message.attachments:
        return

    for attachment in message.attachments:
        if not attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            continue

        thread = None
        sent_messages: list[discord.Message] = []

        try:
            # ✅ Thread PRIVADA real (discord.py 2.6.4)
            thread = await message.channel.create_thread(
                name=f"QR de {message.author.name}",
                message=message,
                type=discord.ChannelType.private_thread
            )

            # adiciona o autor na thread privada
            await thread.add_user(message.author)

            # baixa a imagem
            r = requests.get(attachment.url, timeout=20)
            r.raise_for_status()

            decoded_list = decode_qr_zxing(r.content)

            if decoded_list:
                texto = "\n".join([f"**{i}.** {d}" for i, d in enumerate(decoded_list, start=1)])
                m = await thread.send(
                    f"🔗 **QR encontrado:**\n{texto}\n\n⏳ Apaga em {DELETE_AFTER}s"
                )
                sent_messages.append(m)
            else:
                m = await thread.send(
                    f"❌ **Nenhum QR Code encontrado nessa imagem.**\n\n⏳ Apaga em {DELETE_AFTER}s"
                )
                sent_messages.append(m)

            # espera e apaga
            await asyncio.sleep(DELETE_AFTER)

            # apaga mensagens do bot na thread
            for m in sent_messages:
                try:
                    await m.delete()
                except (discord.Forbidden, discord.NotFound):
                    pass

            # apaga a mensagem original (imagem)
            try:
                await message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass

            # apaga a thread inteira (se não der, arquiva/trava)
            try:
                await thread.delete()
            except (discord.Forbidden, discord.NotFound):
                try:
                    await thread.edit(archived=True, locked=True)
                except:
                    pass

        except Exception as e:
            # aviso simples no canal (sem vazar detalhes)
            try:
                await message.channel.send(f"⚠️ {message.author.mention} erro ao processar o QR.")
            except:
                pass
            print("Erro:", repr(e))

        break  # processa só a primeira imagem

    await bot.process_commands(message)


bot.run(DISCORD_TOKEN)
