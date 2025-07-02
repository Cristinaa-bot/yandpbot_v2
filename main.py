import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# === НАСТРОЙКИ ===
TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [7457586608, 7273958700, 6774952360]  # новые админы
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# === СОСТОЯНИЯ ===
class ProfileStates(StatesGroup):
    text_block = State()
    photos = State()

# === ХРАНИЛИЩЕ ВРЕМЕННОЕ ДЛЯ ФОТО ===
photo_storage = {}

# === КНОПКИ ГОЛОСОВАНИЯ ===
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

# === КОМАНДА /START ===
@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    await message.answer("Benvenuto! Usa /newprofile per creare un profilo.")

# === КОМАНДА /NEWPROFILE ===
@dp.message(F.text == "/newprofile")
async def cmd_newprofile(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer("⛔ Solo gli amministratori possono creare profili.")
        return
    await message.answer("✍️ Invia ora 8 righe di testo (nome, età, città, nazionalità, date, disponibilità, preferenze, numero WhatsApp).")
    await state.set_state(ProfileStates.text_block)

# === ПОЛУЧЕНИЕ 8 СТРОК ТЕКСТА ===
@dp.message(ProfileStates.text_block)
async def get_text_data(message: types.Message, state: FSMContext):
    lines = message.text.strip().split('\n')
    if len(lines) < 8:
        await message.answer("❌ Devi inviare esattamente 8 righe.")
        return
    await state.update_data(
        name=lines[0],
        age=lines[1],
        city=lines[2],
        nationality=lines[3],
        dates=lines[4],
        availability=lines[5],
        preferences=lines[6],
        whatsapp=lines[7]
    )
    await state.set_state(ProfileStates.photos)
    await message.answer("📸 Ora invia 5 foto (tutte insieme preferibilmente).")

# === ОБРАБОТКА ФОТОГРАФИЙ — НОВЫЙ БЛОК ===
@dp.message(ProfileStates.photos, F.photo)
async def handle_photos(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    photo_id = message.photo[-1].file_id

    if user_id not in photo_storage:
        photo_storage[user_id] = []

    photo_storage[user_id].append(photo_id)

    if len(photo_storage[user_id]) == 5:
        await state.update_data(photos=photo_storage[user_id])
        photo_storage.pop(user_id, None)
        await message.answer("✅ Tutte le foto ricevute. Invia /done per pubblicare il profilo.")
    elif len(photo_storage[user_id]) < 5:
        await message.answer(f"📸 Foto {len(photo_storage[user_id])}/5 ricevuta. Continua...")
    else:
        await message.answer("❌ Hai inviato più di 5 foto. Riprova da capo.")
        photo_storage[user_id] = []

# === КОМАНДА /DONE ===
@dp.message(F.text == "/done")
async def finalize_profile(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer("⛔ Solo gli amministratori possono finalizzare il profilo.")
        return

    data = await state.get_data()

    if not all(k in data for k in ["name", "age", "city", "nationality", "dates", "availability", "preferences", "whatsapp", "photos"]):
        await message.answer("❌ I dati del profilo sono incompleti.")
        return

    caption = (
        f"<b>{data['name']}, {data['age']}</b>\n"
        f"{data['nationality']}\n"
        f"<b>Date:</b> {data['dates']}\n"
        f"<b>Disponibilità:</b> {data['availability']}\n"
        f"<b>Preferenze:</b> {data['preferences']}\n"
        f"<b>Città:</b> {data['city']}\n"
        f"<b>WhatsApp:</b> <a href='https://wa.me/{data['whatsapp'].replace('+', '').replace(' ', '')}'>Contatto</a>"
    )

    for i, photo_id in enumerate(data["photos"]):
        if i == 0:
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=photo_id,
                caption=caption,
                reply_markup=vote_kb(profile_id="123"),  # ID placeholder
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        else:
            await bot.send_photo(chat_id=message.chat.id, photo=photo_id)

    await message.answer("✅ Profilo pubblicato con successo!")
    await state.clear()

# === ЗАПУСК ===
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
