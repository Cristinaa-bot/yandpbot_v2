import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import asyncio

API_TOKEN = "8146798235:AAG-JTJOjHaljEDGBs_hlMjMpVbyw6Ih1Qo"
ADMINS = [7457586608, 7273958700, 6774952360]

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

class Profile(StatesGroup):
    text = State()
    photos = State()

profiles = {}
photo_buffer = {}

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Milano")],
        [KeyboardButton(text="Roma")],
        [KeyboardButton(text="Firenze")]
    ], resize_keyboard=True)
    await message.answer("📍 Seleziona la città:", reply_markup=kb)

@dp.message(Command("newprofile"))
async def new_profile(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return await message.answer("⛔ Solo gli admin possono usare questo comando.")
    await state.set_state(Profile.text)
    await message.answer("📝 Invia le 8 righe del profilo:")

@dp.message(Profile.text)
async def process_text(message: Message, state: FSMContext):
    text = message.text.strip().split("\n")
    if len(text) != 8:
        return await message.answer("❌ Devi inviare esattamente 8 righe di testo.")
    user_id = message.from_user.id
    profiles[user_id] = {"data": text, "photos": []}
    await state.set_state(Profile.photos)
    await message.answer("📸 Invia 5 foto come album (tutte insieme).")

@dp.message(Profile.photos)
async def process_photos(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not message.media_group_id:
        return await message.answer("❗ Invia tutte le 5 foto insieme, come album.")
    if user_id not in photo_buffer:
        photo_buffer[user_id] = []
    photo_buffer[user_id].append(message.photo[-1].file_id)

@dp.message(Command("done"))
async def done_profile(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        return await message.answer("⛔ Solo gli admin possono usare questo comando.")
    profile = profiles.get(user_id)
    photos = photo_buffer.get(user_id)
    if not profile or not photos or len(photos) != 5:
        return await message.answer("⚠️ Profilo incompleto o mancano le 5 foto.")
    text = "\n".join(profile["data"])
    whatsapp_line = profile["data"][-1].strip()
    if whatsapp_line.startswith("+"):
        wa_link = f"https://wa.me/{whatsapp_line.replace('+', '').replace(' ', '')}"
        text = text.replace(whatsapp_line, f"<a href='{wa_link}'>{whatsapp_line}</a>")
    media = types.MediaGroup()
    for pid in photos:
        media.attach_photo(pid)
    await bot.send_media_group(chat_id=message.chat.id, media=media)
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🌟 Pulizia")],
        [KeyboardButton(text="💅 Bellezza")],
        [KeyboardButton(text="🍷 Servizio")],
        [KeyboardButton(text="📍 Indirizzo")]
    ], resize_keyboard=True)
    await message.answer(text, reply_markup=kb, disable_web_page_preview=True)
    await message.answer("✅ Profilo pubblicato con successo!")
    await state.clear()
    profiles.pop(user_id, None)
    photo_buffer.pop(user_id, None)

@dp.message()
async def city_filter(message: Message):
    city = message.text.strip()
    if city not in ["Milano", "Roma", "Firenze"]:
        return
    await message.answer("🔍 Nessun profilo disponibile in questa città.\nNuovi arrivi in arrivo, resta sintonizzato!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
