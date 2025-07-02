import logging
fimport logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import asyncio

API_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Админы
ADMINS = [7457586608, 7273958700, 6774952360]

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

class Profile(StatesGroup):
    text = State()
    photos = State()
    whatsapp = State()

photo_storage = {}

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Milano"), KeyboardButton(text="Roma"), KeyboardButton(text="Firenze")]
        ],
        resize_keyboard=True
    )
    await message.answer("👋 Benvenuto! Seleziona la città per vedere i profili disponibili:", reply_markup=keyboard)

@dp.message(Command("newprofile"))
async def new_profile(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer("⛔️ Solo gli amministratori possono creare profili.")
        return
    await message.answer("✍️ Invia 8 righe con le seguenti informazioni separate da 'Invio':\n1. Nome\n2. Età\n3. Città\n4. Nazionalità\n5. Date\n6. Disponibilità\n7. Preferenze\n8. WhatsApp")
    await state.set_state(Profile.text)

@dp.message(Profile.text)
async def process_text(message: types.Message, state: FSMContext):
    lines = message.text.strip().split("\n")
    if len(lines) != 8:
        await message.answer("⚠️ Invia esattamente 8 righe di testo.")
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
    await message.answer("📸 Invia 5 foto insieme (come album).")

@dp.message(Profile.photos, F.media_group_id)
async def handle_album(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in photo_storage:
        photo_storage[user_id] = []
    photo_storage[user_id].append(message.photo[-1].file_id)

@dp.message(Profile.photos)
async def finish_album(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in photo_storage or len(photo_storage[user_id]) < 5:
        await message.answer(f"📸 Foto {len(photo_storage.get(user_id, []))}/5 ricevuta. Continua...")
        return

    data = await state.get_data()
    data["photos"] = photo_storage[user_id][:5]
    await state.update_data(**data)
    photo_storage.pop(user_id, None)

    await message.answer("✅ Tutte le foto ricevute. Invia /done per pubblicare il profilo.")
    await state.set_state(Profile.whatsapp)

@dp.message(Profile.whatsapp, Command("done"))
async def done_profile(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if len(data.get("photos", [])) < 5:
        await message.answer("⚠️ Servono 5 foto prima di completare il profilo.")
        return

    caption = (
        f"<b>{data['name']}, {data['age']}</b>\n"
        f"🌍 {data['nationality']}\n"
        f"📅 {data['dates']}\n"
        f"⏰ {data['availability']}\n"
        f"💖 {data['preferences']}\n"
        f"📍 {data['city']}\n"
        f"📞 <a href='https://wa.me/{data['whatsapp'].replace('+', '').replace(' ', '')}'>Contatto</a>"
    )

    for photo_id in data['photos']:
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=photo_id,
            caption=caption if photo_id == data['photos'][0] else None
        )

    await message.answer("✅ Profilo pubblicato con successo!")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
