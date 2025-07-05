import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import asyncio
import os

# ======= НАСТРОЙКИ =======
API_TOKEN = "8146798235:AAG-JTJOjHaljEDGBs_hlMjMpVbyw6Ih1Qo"
ADMINS = [7457586608, 7273958700, 6774952360]
CITIES = ["Milano", "Roma", "Firenze"]

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# ======= СОСТОЯНИЯ =======
class ProfileForm(StatesGroup):
    collecting_text = State()
    collecting_photos = State()

# ======= КНОПКИ ГОРОДОВ =======
def city_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=city)] for city in CITIES],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# ======= КНОПКИ ГОЛОСОВАНИЯ =======
def vote_keyboard(profile_id="123"):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌟 Pulizia"), KeyboardButton(text="💅 Bellezza")],
            [KeyboardButton(text="🍷 Servizio"), KeyboardButton(text="📍 Indirizzo")]
        ],
        resize_keyboard=True
    )

# ======= ПЕРЕМЕННЫЕ =======
profile_data = {}
photos_buffer = {}

# ======= /START =======
@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    await message.answer("Benvenuto! Seleziona la città per vedere i profili disponibili:", reply_markup=city_keyboard())

@dp.message(F.text.in_(CITIES))
async def city_selected(message: types.Message):
    await message.answer("🔍 Nessun profilo disponibile in questa città. Nuovi arrivi in arrivo, resta sintonizzato!", reply_markup=ReplyKeyboardRemove())

# ======= /NEWPROFILE =======
@dp.message(F.text == "/newprofile")
async def cmd_newprofile(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    await state.set_state(ProfileForm.collecting_text)
    await message.answer("✍️ Invia 8 righe di testo (nome, età, città, nazionalità, date, disponibilità, preferenze, WhatsApp):")

@dp.message(ProfileForm.collecting_text)
async def handle_profile_text(message: types.Message, state: FSMContext):
    lines = message.text.strip().split("\n")
    if len(lines) != 8:
        await message.answer("⚠️ Invia esattamente 8 righe di testo.")
        return
    profile_data[message.from_user.id] = {
        "name": lines[0],
        "age": lines[1],
        "city": lines[2],
        "nationality": lines[3],
        "dates": lines[4],
        "availability": lines[5],
        "preferences": lines[6],
        "whatsapp": lines[7],
    }
    photos_buffer[message.from_user.id] = []
    await state.set_state(ProfileForm.collecting_photos)
    await message.answer("📸 Invia 5 foto come album:")

@dp.message(ProfileForm.collecting_photos, F.content_type == "photo")
async def handle_photos(message: types.Message):
    if message.from_user.id not in photos_buffer:
        return
    if not message.media_group_id:
        await message.answer("⚠️ Invia tutte e 5 le foto insieme, come album.")
        return
    photos_buffer[message.from_user.id].append(message.photo[-1].file_id)

# ======= /DONE =======
@dp.message(F.text == "/done")
async def cmd_done(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    profile = profile_data.get(message.from_user.id)
    photos = photos_buffer.get(message.from_user.id, [])

    if not profile or len(photos) != 5:
        await message.answer("⚠️ Profilo incompleto. Assicurati di inviare 5 foto.")
        return

    text = (
        f"<b>{profile['name']}, {profile['age']}</b>\n"
        f"{profile['nationality']} — {profile['preferences']}\n"
        f"<b>Date:</b> {profile['dates']}\n"
        f"<b>Disponibilità:</b> {profile['availability']}\n"
        f"<b>Città:</b> {profile['city']}\n"
        f"<b>WhatsApp:</b> <a href='https://wa.me/{profile['whatsapp'].replace('+','').replace(' ', '')}'>Contatto</a>"
    )

    media = [types.InputMediaPhoto(media=photo) for photo in photos]
    media[0].caption = text
    media[0].parse_mode = "HTML"

    await bot.send_media_group(chat_id=message.chat.id, media=media)
    await message.answer("✅ Profilo pubblicato con successo!", reply_markup=vote_keyboard())
    
    await state.clear()
    profile_data.pop(message.from_user.id, None)
    photos_buffer.pop(message.from_user.id, None)

# ======= ЗАПУСК =======
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
