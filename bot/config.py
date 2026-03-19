import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN não foi encontrado no arquivo .env")


CANAL_QR_ID = 1461658108081209406
DELETE_AFTER = 60