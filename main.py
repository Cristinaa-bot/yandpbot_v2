import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())


@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer("📸 Invia le foto (max 6), poi manda descrizione in 2 linee")


@dp.message(F.text == "/newprofile")
async def cmd_newprofile(message: Message):
    await message.answer("📬 Invia i dettagli del profilo. (Примерная метка создания анкеты)")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
