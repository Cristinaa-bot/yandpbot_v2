import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
import os

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(commands=["start"])
async def cmd_start(message: Message):
   await update.message.reply_text("Invia le foto (max 5), poi manda descrizione in 7 linee:")
@dp.message(commands=["newprofile"])
async def cmd_newprofile(message: Message):
    await message.answer("📝 Invia i dettagli del profilo. (Примерная логика создания анкеты)")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
