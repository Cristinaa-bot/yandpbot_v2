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
ADMINS = [7457586608, 7273958700, 6774952360]  # Новые админы
CITIES = ["Milano", "Roma", "Firenze"]

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# === STATES ===
class Profile(StatesGroup):
    waiting_text = State()
    waiting_photos = State()

# === KEYBOARDS ===
def cities_kb():
    buttons = [InlineKeyboardButton(text=city, callback_data=f"city:{city}") for city in CITIES]
    return InlineKeyboardMarkup(inline_keyboard=[[btn] for btn in buttons])

def vote_kb(profile_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✨ Pulizia", callback_data=f"vote:{profile_id}:pulizia")],
            [InlineKeyboardButton(text="💋 Bellezza", callback_data=f"vote:{profile_id}:bellezza")],
            [InlineKeyboardButton(text="🍷 Servizio", callback_data=f"vote:{profile_id}:servizio")],
            [InlineKeyboardButton(text="📍 Indirizzo", callback_data=f"vote:{profile_id}:indirizzo")]
        ]
    )

# === HANDLERS ===
@router.message(F.text == "/start")
async def cmd_start(message: types.Message):
    await message.answer("Benvenuto! Seleziona la città per vedere i profili disponibili:", reply_markup=cities_kb())

@router.callback_query(F.data.startswith("city:"))
async def handle_city_selection(callback: types.CallbackQuery):
    await callback.message.answer("🔍 Nessun profilo disponibile in questa città. Nuovi arrivi in arrivo, resta sintonizzato!")

@router.message(F.text == "/newprofile")
async def new_profile(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Solo gli amministratori possono aggiungere profili.")
        return
    await state.set_state(Profile.waiting_text)
    await message.answer("📝 Invia i dettagli del profilo.\n(Примерная матка создания анкеты)")

@router.message(Profile.waiting_text)
async def receive_profile_text(message: types.Message, state: FSMContext):
    lines = message.text.strip().split('\n')
    if len(lines) < 8:
        await message.answer("❌ Devi inviare 8 righe di testo (nome, età, città, ecc...)")
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
        "description": "\n".join(lines[3:7])
    }

    await state.update_data(profile=data, photos=[])
    await state.set_state(Profile.waiting_photos)
    await message.answer("📸 Invia 5 foto del profilo, una per una:")

@router.message(Profile.waiting_photos, F.photo)
async def receive_photos(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)

    if len(photos) < 5:
        await state.update_data(photos=photos)
        await message.answer(f"✅ Foto ricevuta ({len(photos)}/5). Invia un'altra:")
    else:
        profile = data["profile"]
        profile_text = (
            f"<b>{profile['name']}, {profile['age']}</b>\n"
            f"{profile['description']}\n\n"
            f"📍 Città: <b>{profile['city']}</b>\n"
            f"📞 WhatsApp: <a href='https://wa.me/{profile['whatsapp']}'>Contatto</a>"
        )

        await bot.send_photo(
            chat_id=message.chat.id,
            photo=photos[0],
            caption=profile_text,
            reply_markup=vote_kb(profile_id="123"),
            parse_mode="HTML"
        )

        await state.clear()
        await message.answer("✅ Profilo pubblicato con successo!")

@router.message(F.text == "/done")
async def profile_done(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])

    if len(photos) < 5:
        await message.answer("❗️Devi inviare 5 foto prima di completare il profilo.")
        return

    profile = data["profile"]
    text = (
        f"<b>{profile['name']}, {profile['age']}</b>\n"
        f"{profile['description']}\n\n"
        f"📍 Città: <b>{profile['city']}</b>\n"
        f"📞 WhatsApp: <a href='https://wa.me/{profile['whatsapp']}'>Contatto</a>"
    )

    await bot.send_photo(
        chat_id=message.chat.id,
        photo=photos[0],
        caption=text,
        reply_markup=vote_kb(profile_id="123"),
        parse_mode="HTML"
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
