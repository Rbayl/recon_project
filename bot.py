import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from dotenv import load_dotenv
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("subenum-bot")

# ===== LOAD ENV =====
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN belum diset!")

# ===== PATH =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(BASE_DIR, "sub_runner.py")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# ===== SIMPLE LOCK (ANTI SPAM) =====
RUNNING = set()

@dp.message(Command("start"))
async def start(msg: Message):
    await msg.answer(
        "🕵️ Subdomain Enumeration Bot\n\n"
        "Usage:\n"
        "/subenum domain.com"
    )

@dp.message(Command("subenum"))
async def subenum(msg: Message):
    user_id = msg.from_user.id
    args = msg.text.split()

    if len(args) != 2:
        return await msg.reply("❌ Usage: /subenum domain.com")

    if user_id in RUNNING:
        logger.warning(f"JOB STILL RUNNING | USER={user_id}")
        return await msg.reply("⏳ Scan kamu masih berjalan, tunggu selesai.")


    domain = args[1]
    logger.info(
        f"USER={msg.from_user.id} "
        f"USERNAME=@{msg.from_user.username} "
        f"CMD=/subenum "
        f"DOMAIN={domain}"
    )
    RUNNING.add(user_id)
    logger.info(f"SCAN START | USER={user_id} | DOMAIN={domain}")

    await msg.reply(
        f"⏳ Running subdomain enum for `{domain}`",
        parse_mode="Markdown"
    )

    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", RUNNER, domain,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            err = stderr.decode().strip()
            if not err:
                err = "Unknown error"
            logger.error(
                f"SCAN ERROR | USER={user_id} | DOMAIN={domain} | ERROR={err}"
            )
            return await msg.reply(
                f"❌ Scan error:\n```{err[:3500]}```",
                parse_mode="Markdown"
            )

        result_path = stdout.decode().strip()
        alive_path = os.path.join(
            os.path.dirname(result_path),
            f"alive_httpx_{domain}.txt"
        )

        if os.path.exists(alive_path):
            await msg.reply_document(
                FSInputFile(alive_path),
                caption=f"✅ Alive Subdomain for `{domain}`",
                parse_mode="Markdown"
            )

        if not os.path.exists(result_path):
            return await msg.reply("❌ Output file tidak ditemukan")

        await msg.reply_document(
            FSInputFile(result_path),
            caption=f"✅ Subdomain result for `{domain}`",
            parse_mode="Markdown"
        )
        

    except Exception as e:
        await msg.reply(f"❌ Exception:\n```{str(e)}```", parse_mode="Markdown")

    finally:
        RUNNING.discard(user_id)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
