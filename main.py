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

profiles = {}
album_buffer = {}

@dp.message(CommandStart())
async def cmd_start(message: Message):
    if message.from_user.id in ADMINS:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="/newprofile")],
                [KeyboardButton(text="Milano")],
                [KeyboardButton(text="Roma")],
                [KeyboardButton(text="Firenze")],
            ],
            resize_keyboard=True,
        )
        await message.answer("Benvenuto! Usa /newprofile per creare un profilo.", reply_markup=keyboard)
    else:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Milano")],
                [KeyboardButton(text="Roma")],
                [KeyboardButton(text="Firenze")],
            ],
            resize_keyboard=True,
        )
        await message.answer("👋 Benvenuto! Seleziona la città per vedere i profili disponibili:", reply_markup=keyboard)

@dp.message(Command("newprofile"))
async def cmd_newprofile(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return await message.answer("⛔️ Solo gli amministratori possono creare profili.")
    await state.set_state(Profile.text)
    await message.answer("📋 Invia le 8 righe di testo per il profilo:")

@dp.message(Profile.text)
async def profile_text(message: Message, state: FSMContext):
    lines = message.text.strip().split("\n")
    if len(lines) != 8:
        return await message.answer("❌ Invia esattamente 8 righe di testo.")
    profiles[message.from_user.id] = {
        "data": lines,
        "photos": []
    }
    await state.set_state(Profile.photos)
    await message.answer("📸 Invia 5 foto del profilo (puoi inviarle come album).")

@dp.message(Profile.photos, F.media_group_id)
async def handle_album(message: Message, state: FSMContext):
    user_id = message.from_user.id
    album = album_buffer.get(user_id, [])
    album.append(message.photo[-1].file_id)
    album_buffer[user_id] = album

@dp.message(Profile.photos)
async def handle_photo(message: Message, state: FSMContext):
    user_id = message.from_user.id
    profile = profiles.get(user_id)
    if not profile:
        return await message.answer("❌ Nessun profilo in corso. Usa /newprofile.")
    
    if message.media_group_id:
        album = album_buffer.get(user_id, [])
        if len(album) >= 5:
            profile["photos"] = album[:5]
            await state.clear()
            profiles[user_id] = profile
            album_buffer.pop(user_id, None)
            return await message.answer("✅ Tutte le foto ricevute. Invia /done per pubblicare il profilo.")
    else:
        profile["photos"].append(message.photo[-1].file_id)
        if len(profile["photos"]) < 5:
            await message.answer(f"📸 Foto {len(profile['photos'])}/5 ricevuta. Continua...")
        if len(profile["photos"]) == 5:
            await state.clear()
            await message.answer("✅ Tutte le foto ricevute. Invia /done per pubblicare il profilo.")

@dp.message(Command("done"))
async def finish_profile(message: Message, state: FSMContext):
    user_id = message.from_user.id
    profile = profiles.get(user_id)
    if not profile:
        return await message.answer("❌ Nessun profilo da pubblicare.")
    
    text = "\n".join(profile["data"])
    media = types.MediaGroup()
    for photo_id in profile["photos"]:
        media.attach_photo(photo_id)
    await bot.send_media_group(chat_id=message.chat.id, media=media)
    await bot.send_message(chat_id=message.chat.id, text=f"<b>{text}</b>\n👉 <a href='https://wa.me/{profile['data'][7].replace('+', '').replace(' ', '')}'>Scrivi su WhatsApp</a>", disable_web_page_preview=True)
    await message.answer("✅ Profilo pubblicato con successo!")

    await state.clear()
    profiles.pop(user_id, None)
    album_buffer.pop(user_id, None)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
