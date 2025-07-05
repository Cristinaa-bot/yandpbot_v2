import logging
import os
from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.enums import ParseMode
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

API_TOKEN = "8146798235:AAG-JTJOjHaljEDGBs_hlMjMpVbyw6Ih1Qo"
ADMINS = [7457586608, 7273958700, 6774952360]
CITIES = ["Milano", "Roma", "Firenze"]

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# === FSM ===
class ProfileFSM(StatesGroup):
    text = State()
    photos = State()

# === КНОПКИ ===
def cities_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=city)] for city in CITIES],
        resize_keyboard=True
    )

def vote_kb(profile_id="0"):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌟 Pulizia"), KeyboardButton(text="💅 Bellezza")],
            [KeyboardButton(text="🍷 Servizio"), KeyboardButton(text="📍 Indirizzo")]
        ],
        resize_keyboard=True
    )

# === START ===
@router.message(F.text == "/start")
async def cmd_start(message: types.Message):
    await message.answer("📍 Seleziona la città:", reply_markup=cities_kb())

@router.message(F.text.in_(CITIES))
async def handle_city(message: types.Message):
    await message.answer("🔍 Nessun profilo disponibile in questa città. Nuovi arrivi in arrivo, resta sintonizzato!")

# === NEW PROFILE ===
@router.message(F.text == "/newprofile")
async def cmd_newprofile(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    await state.set_state(ProfileFSM.text)
    await message.answer("✍️ Invia 8 righe di testo (nome, età, città, ecc.)")

@router.message(ProfileFSM.text)
async def get_text_block(message: types.Message, state: FSMContext):
    lines = message.text.strip().split("\n")
    if len(lines) != 8:
        await message.answer("❌ Devi inviare esattamente 8 righe di testo.")
        return
    await state.update_data(text_lines=lines)
    await state.set_state(ProfileFSM.photos)
    await message.answer("📸 Invia ora 5 foto (tutte insieme, come album)")

@router.message(ProfileFSM.photos, F.media_group_id)
async def receive_album(message: types.Message, state: FSMContext):
    data = await state.get_data()
    album = data.get("album", [])
    album.append(message.photo[-1].file_id)
    await state.update_data(album=album)

@router.message(ProfileFSM.photos, F.text == "/done")
async def publish_profile(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return

    data = await state.get_data()
    text_lines = data.get("text_lines")
    photos = data.get("album", [])

    if not text_lines or len(photos) != 5:
        await message.answer("❌ Controlla di aver inviato 8 righe di testo e 5 foto.")
        return

    name, age, city, nationality, dates, availability, likes, whatsapp = text_lines

    caption = (
        f"<b>{name}, {age}</b>\n"
        f"<i>{nationality}</i>\n"
        f"{likes}\n\n"
        f"<b>📍 Città:</b> {city}\n"
        f"<b>🗓 Date:</b> {dates}\n"
        f"<b>⏰:</b> {availability}\n"
        f"<b>📞 WhatsApp:</b> <a href='https://wa.me/{whatsapp.replace('+', '').replace(' ', '')}'>Contatto</a>"
    )

    # Отправим как альбом
    media_group = []
    for idx, file_id in enumerate(photos):
        if idx == 0:
            media_group.append(types.InputMediaPhoto(media=file_id, caption=caption, parse_mode="HTML"))
        else:
            media_group.append(types.InputMediaPhoto(media=file_id))
    await bot.send_media_group(chat_id=message.chat.id, media=media_group)

    # Голосование
    await bot.send_message(
        chat_id=message.chat.id,
        text="🗳 Vota il profilo:",
        reply_markup=vote_kb()
    )

    await message.answer("✅ Profilo pubblicato con successo!")
    await state.clear()

# === LAUNCH ===
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
