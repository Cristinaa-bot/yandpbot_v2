import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import Router
import asyncio
import os

# ======= CONFIG =======
TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [7457586608, 7273958700, 6774952360]
CITIES = ["Milano", "Roma", "Firenze"]
# =======================

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# ======= STATES =======
class Profile(StatesGroup):
    data_block = State()
    photos = State()

# ======= KEYBOARDS =======
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

# ======= HANDLERS =======
@router.message(F.text == "/start")
async def cmd_start(message: types.Message):
    await message.answer("Benvenuto! Seleziona la città per vedere i profili disponibili:", reply_markup=cities_kb())

@router.callback_query(F.data.startswith("city:"))
async def handle_city_selection(callback: types.CallbackQuery):
    await callback.message.answer("🔍 Nessun profilo disponibile in questa città. Nuovi arrivi in arrivo, resta sintonizzato!")

@router.message(F.text == "/newprofile")
async def new_profile(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer("Solo gli amministratori possono aggiungere profili.")
        return
    await state.set_state(Profile.data_block)
    await message.answer("✏️ Invia 8 righe di testo (una sotto l’altra):\n\n1. Nome\n2. Età\n3. Città\n4. Nazionalità\n5. Date\n6. Disponibilità\n7. Preferenze\n8. WhatsApp")

@router.message(Profile.data_block)
async def handle_text_block(message: types.Message, state: FSMContext):
    lines = message.text.strip().split("\n")
    if len(lines) < 8:
        await message.answer("⚠️ Devi inviare esattamente 8 righe di testo.")
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
        "photos": []
    }
    await state.update_data(**data)
    await state.set_state(Profile.photos)
    await message.answer("📸 Invia 5 foto (una per volta).")

@router.message(Profile.photos, F.photo)
async def handle_photos(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
# Для хранения временных фото
photo_storage = {}

@router.message(Profile.photos)
async def handle_photo_group(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    media_group_id = message.media_group_id

    # Если это часть альбома (альбом = все 5 фото вместе)
    if media_group_id:
        if user_id not in photo_storage:
            photo_storage[user_id] = []
        photo_storage[user_id].append(message.photo[-1].file_id)

        if len(photo_storage[user_id]) == 5:
            await state.update_data(photo_ids=photo_storage[user_id])
            photo_storage.pop(user_id, None)
            await state.set_state(Profile.whatsapp)
            await message.answer("📞 Inserisci il link WhatsApp (senza anteprima):")
    else:
        await message.answer("📸 Invia 5 foto insieme (come album, non separatamente).")
@router.message(Profile.photos, F.photo)
async def handle_photo_album(message: types.Message, state: FSMContext):
    data = await state.get_data()
    album_id = message.media_group_id
    photos = data.get("photos", [])

    if album_id:
        photos.append(message.photo[-1].file_id)
        await state.update_data(photos=photos)

        if len(photos) >= 5:
            await message.answer("✅ Tutte le 5 foto ricevute. Ora invia /done per pubblicare il profilo.")
    else:
        photos.append(message.photo[-1].file_id)
        await state.update_data(photos=photos)
        await message.answer(f"📸 Foto ricevuta ({len(photos)}/5). Invia altre o /done.")

@router.message(Profile.photos, F.text == "/done")
async def done_profile(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if len(data.get("photos", [])) < 5:
        await message.answer("⚠️ Servono 5 foto prima di completare il profilo.")
        return

    caption = (
        f"<b>{data['name']}, {data['age']}</b>\n"
        f"{data['nationality']}\n"
        f"{data['dates']}\n"
        f"{data['availability']}\n"
        f"{data['preferences']}\n\n"
        f"<b>Città:</b> {data['city']}\n"
        f"<b>WhatsApp:</b> <a href='https://wa.me/{data['whatsapp'].replace('+', '').replace(' ', '')}'>Contatto</a>"
    )

    for photo_id in data['photos']:
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=photo_id,
            caption=caption if photo_id == data['photos'][0] else None,
            reply_markup=vote_kb("123"),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

    await state.clear()
    await message.answer("✅ Profilo pubblicato con successo!")

# ======= LAUNCH =======
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
