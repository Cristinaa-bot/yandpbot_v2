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
    whatsapp = State()

# === KEYBOARDS ===
def cities_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=city, callback_data=city)] for city in CITIES
    ])

def vote_kb(profile_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Pulizia ⭐️", callback_data=f"vote:clean:{profile_id}")],
        [InlineKeyboardButton(text="Bellezza 💋", callback_data=f"vote:beauty:{profile_id}")],
        [InlineKeyboardButton(text="Servizio 💎", callback_data=f"vote:service:{profile_id}")],
        [InlineKeyboardButton(text="Indirizzo 📍", callback_data=f"vote:location:{profile_id}")]
    ])

# === START ===
@router.message(F.text == "/start")
async def start_cmd(message: types.Message):
    await message.answer(
        "👋 Benvenuto! Seleziona la città per vedere i profili disponibili:",
        reply_markup=cities_kb()
    )

# === NEW PROFILE (ADMINS ONLY) ===
@router.message(F.text == "/newprofile")
async def new_profile(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Benvenuto! Solo gli admin possono creare nuovi profili.")
        return
    await message.answer("✍️ Invia 8 строк (имя, возраст, город, национальность, даты, доступность, предпочтения, номер WhatsApp):")
    await state.set_state(ProfileStates.data_block)

@router.message(ProfileStates.data_block)
async def get_text_data(message: types.Message, state: FSMContext):
    lines = message.text.strip().split("\n")
    if len(lines) != 8:
        await message.answer("⚠️ Devi inviare esattamente 8 righe.")
        return
    data = {
        "name": lines[0],
        "age": lines[1],
        "city": lines[2],
        "nationality": lines[3],
        "dates": lines[4],
        "availability": lines[5],
        "preferences": lines[6],
        "whatsapp": lines[7]
    }
    await state.update_data(data=data)
    await message.answer("📸 Invia 5 foto tutte insieme (come album, non separatamente).")
    await state.set_state(ProfileStates.photos)

@router.message(ProfileStates.photos, F.media_group_id)
async def handle_album(message: types.Message, state: FSMContext):
    album = await state.get_data()
    photos = album.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)

@router.message(ProfileStates.photos, ~F.media_group_id)
async def handle_non_album(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    if len(photos) != 5:
        await message.answer(f"⚠️ Hai inviato {len(photos)} foto. Devono essere 5.")
        return
    await message.answer("✅ Tutte le foto ricevute. Invia /done per pubblicare il profilo.")

@router.message(F.text == "/done")
async def done_profile(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    profile = data.get("data", {})

    if len(photos) < 5:
        await message.answer("⚠️ Servono 5 foto per completare il profilo.")
        return

    text = (
        f"<b>{profile['name']}, {profile['age']}</b>\n"
        f"{profile['nationality']}\n"
        f"📅 {profile['dates']}\n"
        f"⏰ {profile['availability']}\n"
        f"❤️ {profile['preferences']}\n"
        f"📍 <b>Città:</b> {profile['city']}\n"
        f"📞 WhatsApp: <a href='https://wa.me/{profile['whatsapp'].replace('+','').replace(' ','')}'><b>Contatto</b></a>"
    )

    for photo in photos:
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=photo,
            caption=text if photo == photos[0] else None,
            reply_markup=vote_kb(profile_id="123"),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

    await state.clear()
    await message.answer("✅ Profilo pubblicato con successo!")

# === RUN ===
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
