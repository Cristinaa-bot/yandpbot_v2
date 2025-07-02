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
    text = State()
    photos = State()

# ======= KEYBOARDS =======
def cities_kb():
    buttons = [InlineKeyboardButton(text=city, callback_data=f"city:{city}") for city in CITIES]
    return InlineKeyboardMarkup(inline_keyboard=[[btn] for btn in buttons])

def vote_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌟 Pulizia", callback_data="vote:pulizia"),
                InlineKeyboardButton(text="💅 Bellezza", callback_data="vote:bellezza"),
            ],
            [
                InlineKeyboardButton(text="🍷 Servizio", callback_data="vote:servizio"),
                InlineKeyboardButton(text="📍 Indirizzo", callback_data="vote:indirizzo"),
            ]
        ]
    )

# ======= HANDLERS =======
@router.message(F.text == "/start")
async def cmd_start(message: types.Message):
    await message.answer("Benvenuto! Seleziona la città per vedere i profili disponibili:", reply_markup=cities_kb())

@router.callback_query(F.data.startswith("city:"))
async def handle_city_selection(callback: types.CallbackQuery):
    city = callback.data.split(":")[1]
    await callback.message.answer("🔍 Nessun profilo disponibile in questa città. Nuovi arrivi in arrivo, resta sintonizzato!")

@router.message(F.text == "/newprofile")
async def new_profile(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer("Solo gli amministratori possono aggiungere profili.")
        return
    await state.set_state(Profile.text)
    await message.answer("✍️ Invia 8 righe di testo:\nNome\nEtà\nCittà\nNazionalità\nDate\nDisponibilità\nPreferenze\nNumero WhatsApp")

@router.message(Profile.text)
async def handle_text(message: types.Message, state: FSMContext):
    lines = message.text.strip().split("\n")
    if len(lines) != 8:
        await message.answer("❗️Per favore, invia esattamente 8 righe.")
        return
    await state.update_data(profile_lines=lines)
    await state.set_state(Profile.photos)
    await message.answer("📸 Ora invia 5 foto in un unico messaggio (album).")

@router.message(Profile.photos, F.media_group_id)
async def handle_photos(message: types.Message, state: FSMContext):
    data = await state.get_data()
    album = data.get("album", [])
    album.append(message.photo[-1].file_id)
    await state.update_data(album=album)

@router.message(Profile.photos, F.text == "/done")
async def handle_done(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lines = data.get("profile_lines", [])
    album = data.get("album", [])

    if not lines or len(album) != 5:
        await message.answer("❗️Assicurati di aver inviato 5 foto e 8 righe di testo prima di usare /done.")
        return

    name, age, city, nationality, dates, availability, likes, whatsapp = lines

    caption = (
        f"<b>{name}, {age}</b>\n"
        f"{nationality}\n"
        f"{dates}\n"
        f"{availability}\n"
        f"{likes}\n\n"
        f"<b>Città:</b> {city}\n"
        f"<b>WhatsApp:</b> <a href='https://wa.me/{whatsapp.replace('+', '').replace(' ', '')}'>Contatto</a>"
    )

    for photo in album[:-1]:
        await bot.send_photo(chat_id=message.chat.id, photo=photo)

    await bot.send_photo(
        chat_id=message.chat.id,
        photo=album[-1],
        caption=caption,
        reply_markup=vote_kb(),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

    await message.answer("✅ Profilo pubblicato con successo!")
    await state.clear()

# ======= LAUNCH =======
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
