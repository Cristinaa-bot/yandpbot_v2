iimport logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")

ADMINS = [7457586608, 7273958700, 6774952360]

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

CITIES = ["Milano", "Roma", "Firenze"]

class ProfileState(StatesGroup):
    waiting_for_text = State()
    waiting_for_photos = State()

def cities_kb():
    buttons = [InlineKeyboardButton(text=city, callback_data=f"city:{city}") for city in CITIES]
    return InlineKeyboardMarkup(inline_keyboard=[[btn] for btn in buttons])

def vote_kb(profile_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌟 Pulizia", callback_data=f"vote:{profile_id}:pulizia"),
                InlineKeyboardButton(text="💅 Bellezza", callback_data=f"vote:{profile_id}:bellezza"),
            ],
            [
                InlineKeyboardButton(text="🍷 Servizio", callback_data=f"vote:{profile_id}:servizio"),
                InlineKeyboardButton(text="📍 Indirizzo", callback_data=f"vote:{profile_id}:indirizzo"),
            ]
        ]
    )

profiles_data = {}

@router.message(F.text == "/start")
async def cmd_start(message: types.Message):
    await message.answer("Benvenuto! Seleziona la città per vedere i profili disponibili:", reply_markup=cities_kb())

@router.callback_query(F.data.startswith("city:"))
async def handle_city_selection(callback: types.CallbackQuery):
    await callback.message.answer("🔍 Nessun profilo disponibile in questa città. Nuovi arrivi in arrivo, resta sintonizzato!")

@router.message(F.text == "/newprofile")
async def cmd_new_profile(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    await message.answer("Invia ora le 8 righe di testo:")
    await state.set_state(ProfileState.waiting_for_text)

@router.message(ProfileState.waiting_for_text)
async def receive_text(message: types.Message, state: FSMContext):
    lines = message.text.strip().split("\n")
    if len(lines) < 8:
        await message.answer("❌ Invia esattamente 8 righe.")
        return
    profile = {
        "name": lines[0],
        "age": lines[1],
        "city": lines[2],
        "nationality": lines[3],
        "dates": lines[4],
        "availability": lines[5],
        "preferences": lines[6],
        "whatsapp": lines[7],
        "photos": []
    }
    await state.update_data(profile=profile)
    await state.set_state(ProfileState.waiting_for_photos)
    await message.answer("📸 Invia ora 5 foto (in un unico invio).")

@router.message(ProfileState.waiting_for_photos, F.media_group_id)
async def receive_album_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    profile = data["profile"]
    photos = profile.get("photos", [])
    photos.append(message.photo[-1].file_id)
    profile["photos"] = photos
    await state.update_data(profile=profile)

@router.message(ProfileState.waiting_for_photos, F.text == "/done")
async def finish_profile(message: types.Message, state: FSMContext):
    data = await state.get_data()
    profile = data["profile"]
    if len(profile.get("photos", [])) < 5:
        await message.answer("❌ Devi inviare 5 foto prima di completare.")
        return
    text = (
        f"<b>{profile['name']}, {profile['age']}</b>\n"
        f"<b>{profile['nationality']}</b>\n"
        f"{profile['preferences']}\n\n"
        f"<b>Date:</b> {profile['dates']}\n"
        f"<b>Disponibilità:</b> {profile['availability']}\n"
        f"<b>Città:</b> {profile['city']}\n"
        f"<b>WhatsApp:</b> <a href='https://wa.me/{profile['whatsapp'].replace('+', '').replace(' ', '')}'>Contatto</a>"
    )
    media = []
    for photo_id in profile["photos"]:
        media.append(types.InputMediaPhoto(media=photo_id))
    media[0].caption = text
    media[0].parse_mode = ParseMode.HTML

    await bot.send_media_group(chat_id=message.chat.id, media=media)
    await message.answer("✅ Profilo pubblicato con successo!")
    await state.clear()

@router.message(ProfileState.waiting_for_photos)
async def fallback_photos(message: types.Message):
    await message.answer("❗️Devi inviare 5 foto come gruppo o digitare /done per completare.")

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
