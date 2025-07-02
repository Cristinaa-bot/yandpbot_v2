import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router
import asyncio

# === ТОКЕН И АДМИНЫ ===
API_TOKEN = "8146798235:AAG-JTJOjHaljEDGBs_hlMjMpVbyw6Ih1Qo"
ADMINS = [7457586608, 7273958700, 6774952360]

# === НАСТРОЙКА БОТА ===
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# === СОСТОЯНИЯ ===
class ProfileState(StatesGroup):
    text = State()
    photos = State()

# === КНОПКИ ГОЛОСОВАНИЯ ===
def vote_kb(profile_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌟 Pulizia", callback_data=f"vote:{profile_id}:pulizia"),
            InlineKeyboardButton(text="💅 Bellezza", callback_data=f"vote:{profile_id}:bellezza"),
        ],
        [
            InlineKeyboardButton(text="🍷 Servizio", callback_data=f"vote:{profile_id}:servizio"),
            InlineKeyboardButton(text="📍 Indirizzo", callback_data=f"vote:{profile_id}:indirizzo"),
        ]
    ])

# === СТАРТ ===
@router.message(F.text == "/start")
async def start_cmd(message: types.Message):
    await message.answer("Benvenuto! Seleziona una città per vedere i profili disponibili.")

# === СОЗДАНИЕ АНКЕТЫ ===
@router.message(F.text == "/newprofile")
async def newprofile_cmd(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer("⚠️ Solo gli amministratori possono creare profili.")
        return
    await message.answer("✏️ Invia le 8 righe di testo (nome, età, città, nazionalità, date, disponibilità, preferenze, WhatsApp):")
    await state.set_state(ProfileState.text)

@router.message(ProfileState.text)
async def get_text(message: types.Message, state: FSMContext):
    lines = message.text.strip().split("\n")
    if len(lines) < 8:
        await message.answer("⚠️ Invia esattamente 8 righe di testo.")
        return
    await state.update_data(text_lines=lines, photos=[])
    await message.answer("📸 Invia 5 foto (tutte insieme come album).")
    await state.set_state(ProfileState.photos)

@router.message(ProfileState.photos, F.content_type == types.ContentType.PHOTO)
async def get_photos(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    if len(photos) >= 5:
        await message.answer("✅ Hai inviato 5 foto. Ora invia /done per pubblicare il profilo.")

@router.message(F.text == "/done")
async def done_profile(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer("⚠️ Solo gli amministratori possono usare questo comando.")
        return
    data = await state.get_data()
    text_lines = data.get("text_lines", [])
    photos = data.get("photos", [])
    if len(text_lines) < 8 or len(photos) < 5:
        await message.answer("⚠️ Profilo incompleto. Assicurati di aver inviato 8 righe di testo e 5 foto.")
        return

    name = text_lines[0]
    age = text_lines[1]
    city = text_lines[2]
    nationality = text_lines[3]
    dates = text_lines[4]
    availability = text_lines[5]
    preferences = text_lines[6]
    whatsapp = text_lines[7]

    caption = (
        f"<b>{name}, {age}</b>\n"
        f"<i>{preferences}</i>\n\n"
        f"<b>Città:</b> {city}\n"
        f"<b>Dal:</b> {dates}\n"
        f"<b>Disponibilità:</b> {availability}\n"
        f"<b>Nazionalità:</b> {nationality}\n"
        f"<b>WhatsApp:</b> <a href='https://wa.me/{whatsapp.replace('+', '').replace(' ', '')}'>Contatto</a>"
    )

    media = [types.InputMediaPhoto(media=photo) for photo in photos]
    media[0].caption = caption
    media[0].parse_mode = "HTML"

    await bot.send_media_group(chat_id=message.chat.id, media=media)
    await message.answer("✅ Profilo pubblicato con successo!")
    await state.clear()

# === ЗАПУСК ===
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
