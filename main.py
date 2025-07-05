import logging
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import os

# === НАСТРОЙКИ ===
API_TOKEN = "8146798235:AAG-JTJOjHaljEDGBs_hlMjMpVbyw6Ih1Qo"
ADMINS = [7457586608, 7273958700, 6774952360]
CITIES = ["Milano", "Roma", "Firenze"]

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# === СОСТОЯНИЯ ===
class Profile(StatesGroup):
    text_block = State()
    photos = State()

# === КНОПКИ ===
def city_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=city)] for city in CITIES],
        resize_keyboard=True
    )

def vote_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌟 Pulizia"), KeyboardButton(text="💅 Bellezza")],
            [KeyboardButton(text="🍷 Servizio"), KeyboardButton(text="📍 Indirizzo")]
        ],
        resize_keyboard=True
    )

# === ОБРАБОТЧИКИ ===

@dp.message(F.text == "/start")
async def start(message: types.Message):
    await message.answer("Benvenuto! Seleziona la città:", reply_markup=city_keyboard())

@dp.message(F.text.in_(CITIES))
async def show_city_profiles(message: types.Message):
    await message.answer(
        "🔍 Nessun profilo disponibile in questa città. Nuovi arrivi in arrivo, resta sintonizzato!",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(F.text == "/newprofile")
async def new_profile(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer("Comando non disponibile.")
        return
    await message.answer("📄 Invia le 8 righe di testo (nome, età, città, ecc.)")
    await state.set_state(Profile.text_block)

@dp.message(Profile.text_block)
async def handle_text_block(message: types.Message, state: FSMContext):
    lines = message.text.strip().split("\n")
    if len(lines) != 8:
        await message.answer("❌ Invia esattamente 8 righe di testo.")
        return
    await state.update_data(text_block=lines, photos=[])
    await state.set_state(Profile.photos)
    await message.answer("📸 Invia 5 foto (una per volta o come album).")

@dp.message(Profile.photos, F.photo)
async def handle_photos(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)

    if len(photos) < 5:
        await message.answer(f"📸 Foto ricevute: {len(photos)}/5. Invia ancora.")
    else:
        await message.answer("✅ Foto ricevute. Ora invia /done per pubblicare.")

@dp.message(F.text == "/done")
async def finish_profile(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer("Comando non disponibile.")
        return
    data = await state.get_data()
    lines = data.get("text_block", [])
    photos = data.get("photos", [])

    if len(lines) != 8 or len(photos) != 5:
        await message.answer("❌ Dati incompleti. Invia 8 righe + 5 foto.")
        return

    name, age, city, nationality, dates, availability, preferences, whatsapp = lines

    caption = (
        f"<b>{name}, {age}</b>\n"
        f"{nationality}, {dates}\n"
        f"{availability}\n"
        f"{preferences}\n\n"
        f"<b>Città:</b> {city}\n"
        f"<b>WhatsApp:</b> <a href='https://wa.me/{whatsapp.replace('+', '').replace(' ', '')}'>Contatto</a>"
    )

    media = [types.InputMediaPhoto(media=photo) for photo in photos]
    media[0].caption = caption
    media[0].parse_mode = "HTML"

    await bot.send_media_group(chat_id=message.chat.id, media=media)
    await message.answer("✅ Profilo pubblicato con successo!", reply_markup=vote_keyboard())
    await state.clear()

# === ЗАПУСК ===
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    def city_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Milano")],
            [KeyboardButton(text="Roma")],
            [KeyboardButton(text="Firenze")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

