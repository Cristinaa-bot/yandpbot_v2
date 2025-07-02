import logging
import os
import asyncio

from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import Router

# === CONFIG ===

TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [7457586608, 7273958700, 6774952360]
CITIES = ["Milano", "Roma", "Firenze"]

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# === STATES ===
class ProfileStates(StatesGroup):
    data_block = State()
    photos = State()

# === KEYBOARDS ===
def cities_kb():
    buttons = [types.KeyboardButton(text=city) for city in CITIES]
    keyboard = types.ReplyKeyboardMarkup(keyboard=[buttons], resize_keyboard=True)
    return keyboard

def approve_kb(profile_id: str):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👍 Pulizia", callback_data=f"vote_clean:{profile_id}")],
        [InlineKeyboardButton(text="👗 Bellezza", callback_data=f"vote_beauty:{profile_id}")],
        [InlineKeyboardButton(text="💁 Servizio", callback_data=f"vote_service:{profile_id}")],
        [InlineKeyboardButton(text="📍 Indirizzo", callback_data=f"vote_address:{profile_id}")]
    ])
    return markup

# === STORAGE ===
profile_data = {}
photo_storage = {}

# === COMMANDS ===
@router.message(F.text == "/start")
async def cmd_start(message: types.Message):
    await message.answer("Benvenuto! Solo gli admin possono creare nuovi profili.")

@router.message(F.text == "/newprofile")
async def new_profile(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer("Accesso negato.")
        return
    await state.set_state(ProfileStates.data_block)
    await message.answer("📋 Invia 8 righe: Nome, Età, Città, Nazionalità, Date, Disponibilità, Preferenze, WhatsApp.")

@router.message(ProfileStates.data_block)
async def receive_data_block(message: types.Message, state: FSMContext):
    lines = message.text.split("\n")
    if len(lines) != 8:
        await message.answer("❌ Invia esattamente 8 righe.")
        return
    data = {
        "name": lines[0],
        "age": lines[1],
        "city": lines[2],
        "nationality": lines[3],
        "dates": lines[4],
        "availability": lines[5],
        "preferences": lines[6],
        "whatsapp": lines[7],
    }
    await state.update_data(data=data, photos=[])
    await state.set_state(ProfileStates.photos)
    await message.answer("📸 Invia 5 foto insieme (come album, non separatamente).")

@router.message(ProfileStates.photos, F.media_group_id)
async def receive_album(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in photo_storage:
        photo_storage[user_id] = []
    photo_storage[user_id].append(message.photo[-1].file_id)

@router.message(ProfileStates.photos)
async def handle_non_album_photos(message: types.Message, state: FSMContext):
    await message.answer("❗ Invia le 5 foto tutte insieme come album (non una per una).")

@router.message(ProfileStates.photos, F.text == "/done")
async def done_profile(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in photo_storage or len(photo_storage[user_id]) != 5:
        await message.answer("⚠️ Servono 5 foto insieme. Invia tutte insieme come album.")
        return
    data = await state.get_data()
    data["photos"] = photo_storage[user_id]
    photo_storage.pop(user_id, None)

    caption = (
        f"<b>{data['name']}, {data['age']}</b>\n"
        f"{data['nationality']}\n"
        f"{data['dates']}\n"
        f"{data['availability']}\n"
        f"{data['preferences']}\n"
        f"<b>Città:</b> {data['city']}\n"
        f"📞 WhatsApp: <a href='https://wa.me/{data['whatsapp'].replace('+', '').replace(' ', '')}'>Contatto</a>"
    )

    for photo_id in data["photos"]:
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=photo_id,
            caption=caption if photo_id == data["photos"][0] else None,
            reply_markup=approve_kb(profile_id="123"),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

    await state.clear()
    await message.answer("✅ Profilo pubblicato con successo!")

# === LAUNCH ===
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
