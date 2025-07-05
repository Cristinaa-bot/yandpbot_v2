import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

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
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Milano")],
            [KeyboardButton(text="Roma")],
            [KeyboardButton(text="Firenze")]
        ],
        resize_keyboard=True
    )
    await message.answer("📍 Seleziona la città:", reply_markup=keyboard)

@dp.message(F.text.in_(["Milano", "Roma", "Firenze"]))
async def city_selected(message: Message):
    await message.answer("🔍 Nessun profilo disponibile in questa città.\nNuovi arrivi in arrivo, resta sintonizzato!")

@dp.message(Command("newprofile"))
async def new_profile(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    await message.answer("📝 Invia le 8 righe di testo per il profilo:")
    await state.set_state(Profile.text)

@dp.message(Profile.text)
async def process_text(message: Message, state: FSMContext):
    lines = message.text.strip().split("\n")
    if len(lines) != 8:
        await message.answer("❌ Devi inviare esattamente 8 righe di testo.")
        return
    user_id = message.from_user.id
    profiles[user_id] = {"data": lines, "photos": []}
    album_buffer[user_id] = []
    await message.answer("📸 Invia ora 5 foto come album.")
    await state.set_state(Profile.photos)

@dp.message(Profile.photos, F.media_group_id)
async def handle_album(message: Message, state: FSMContext):
    user_id = message.from_user.id
    album_buffer[user_id].append(message.photo[-1].file_id)

@dp.message(Profile.photos)
async def save_photos(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in album_buffer or len(album_buffer[user_id]) != 5:
        await message.answer("❌ Devi inviare esattamente 5 foto in un album.")
        return
    profiles[user_id]["photos"] = album_buffer[user_id]
    await message.answer("✅ Foto ricevute. Invia /done per pubblicare il profilo.")

@dp.message(Command("done"))
async def publish_profile(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        return
    profile = profiles.get(user_id)
    if not profile:
        await message.answer("❌ Nessun profilo trovato.")
        return

    text = "\n".join(profile["data"])
    wa_number = profile["data"][-1].replace("+", "").replace(" ", "")
    whatsapp_link = f"[{profile['data'][-1]}](https://wa.me/{wa_number})"

    caption = f"{profile['data'][0]}, {profile['data'][1]}\n{profile['data'][2]}\n" \
              f"{profile['data'][3]}\n{profile['data'][4]}\n{profile['data'][5]}\n" \
              f"{profile['data'][6]}\n📞 {whatsapp_link}"

    media = types.MediaGroup()
    for photo_id in profile["photos"]:
        media.attach_photo(photo_id)
    await bot.send_media_group(chat_id=message.chat.id, media=media)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌟 Pulizia")],
            [KeyboardButton(text="💅 Bellezza")],
            [KeyboardButton(text="🍷 Servizio")],
            [KeyboardButton(text="📍 Indirizzo")]
        ],
        resize_keyboard=True
    )

    await message.answer(caption, reply_markup=keyboard, disable_web_page_preview=True)
    await message.answer("✅ Profilo pubblicato con successo!")

    await state.clear()
    profiles.pop(user_id, None)
    album_buffer.pop(user_id, None)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
