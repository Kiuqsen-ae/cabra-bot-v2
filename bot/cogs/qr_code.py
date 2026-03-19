import io
import asyncio
import aiohttp
import discord
import zxingcpp

from PIL import Image
from discord.ext import commands
from bot.config import CANAL_QR_ID, DELETE_AFTER


def decode_qr_zxing(image_bytes: bytes) -> list[str]:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    results = zxingcpp.read_barcodes(img)

    decoded = []
    for r in results:
        if r.text:
            decoded.append(r.text)

    seen = set()
    uniq = []
    for t in decoded:
        if t not in seen:
            seen.add(t)
            uniq.append(t)

    return uniq


class QRCode(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if message.author.bot:
            return

        if message.channel.id != CANAL_QR_ID:
            return

        if not message.attachments:
            return

        for attachment in message.attachments:

            if not attachment.filename.lower().endswith(
                (".png", ".jpg", ".jpeg", ".webp")
            ):
                continue

            thread = None
            sent_messages = []

            try:
                thread = await message.channel.create_thread(
                    name=f"QR de {message.author.name}",
                    message=message,
                    type=discord.ChannelType.private_thread
                )

                await thread.add_user(message.author)

                async with aiohttp.ClientSession() as session:
                 async with session.get(attachment.url) as resp:
                  image_bytes = await resp.read()

                decoded_list = decode_qr_zxing(image_bytes)
                if decoded_list:

                    texto = "\n".join(
                        [f"**{i}.** {d}" for i, d in enumerate(decoded_list, start=1)]
                    )

                    m = await thread.send(
                        f"🔗 **QR encontrado:**\n{texto}\n\n⏳ Apaga em {DELETE_AFTER}s"
                    )

                    sent_messages.append(m)

                else:

                    m = await thread.send(
                        f"❌ Nenhum QR Code encontrado.\n\n⏳ Apaga em {DELETE_AFTER}s"
                    )

                    sent_messages.append(m)

                await asyncio.sleep(DELETE_AFTER)

                for m in sent_messages:
                    try:
                        await m.delete()
                    except:
                        pass

                try:
                    await message.delete()
                except:
                    pass

                try:
                    await thread.delete()
                except:
                    await thread.edit(archived=True, locked=True)

            except Exception as e:

                try:
                    await message.channel.send(
                        f"⚠️ {message.author.mention} erro ao processar o QR."
                    )
                except:
                    pass

                print("Erro:", repr(e))

            break


async def setup(bot: commands.Bot):
    await bot.add_cog(QRCode(bot))