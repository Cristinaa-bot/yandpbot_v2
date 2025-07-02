import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import asyncio

API_TOKEN = "8146798235:AAG-JTJOjHaljEDGBs_hlMjMpVbyw6Ih1Qo"

ADMINS = [7457586608, 7273958700, 6774952360]

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

class Profile(StatesGroup):
    text = State()
    photos = State()
    done = State()

profiles = {}
album_buffer = {}

@dp.message(CommandStart())
async def cmd_start(message: Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Milano")],
        [KeyboardButton(text="Roma")],
        [KeyboardButton(text="Firenze")]
    ], resize_keyboard=True)
    await message.answer("👋 Benvenuto! Seleziona la città per vedere i profili disponibili:", reply_markup=kb)

@dp.message(Command("newprofile"))
async def cmd_newprofile(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return await message.answer("⛔️ Solo gli amministratori possono creare profili.")
    await message.answer("📋 Invia le 8 righe di testo per il profilo:")
    await state.set_state(Profile.text)

@dp.message(Profile.text)
async def get_profile_text(message: Message, state: FSMContext):
    lines = message.text.strip().split('\n')
    if len(lines) != 8:
        return await message.answer("❗️ Per favore, invia esattamente 8 righe di testo.")
    
    city = lines[2].strip()
    whatsapp = lines[7].strip()
    
    profiles[message.from_user.id] = {
        "data": lines,
        "city": city,
        "whatsapp": whatsapp,
        "photos": []
    }

    album_buffer[message.from_user.id] = []

    await state.set_state(Profile.photos)
    await message.answer("📸 Invia 5 foto (tutte insieme come album).")

@dp.message(Profile.photos, F.media_group_id)
async def handle_album(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in album_buffer:
        album_buffer[user_id] = []
    album_buffer[user_id].append(message.photo[-1].file_id)

@dp.message(Profile.photos)
async def handle_album_end(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in album_buffer and len(album_buffer[user_id]) == 5:
        profiles[user_id]["photos"] = album_buffer[user_id]
        await state.set_state(Profile.done)
        await message.answer("✅ Tutte le foto ricevute. Invia /done per pubblicare il profilo.")
    else:
        await message.answer("⏳ Foto ricevute: {}. Invia 5 foto tutte insieme come album.".format(len(album_buffer.get(user_id, []))))

@dp.message(Command("done"), Profile.done)
async def finalize_profile(message: Message, state: FSMContext):
    user_id = message.from_user.id
    profile = profiles.get(user_id)
    if not profile:
        return await message.answer("❌ Nessun profilo trovato.")
    
    text = "\n".join(profile["data"])
    media = types.MediaGroup()
    for photo_id in profile["photos"]:
        media.attach_photo(photo_id)
    
    await bot.send_media_group(chat_id=message.chat.id, media=media)
    await bot.send_message(chat_id=message.chat.id, text=text + f"\n👉 <a href='https://wa.me/{profile['whatsapp'].replace('+','')}'>Contatta su WhatsApp</a>", disable_web_page_preview=True)
    await message.answer("✅ Profilo pubblicato con successo!")
    
    await state.clear()
    profiles.pop(user_id, None)
    album_buffer.pop(user_id, None)
