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
ADMINS = [7457586608, 7273958700, 6774952360]  # Новые админы
CITIES = ["Milano", "Roma", "Firenze"]
# =======================

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# ======= STATES =======
class Profile(StatesGroup):
    city = State()
    name = State()
    age = State()
    description = State()
    photo = State()
    whatsapp = State()

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
    city = callback.data.split(":")[1]
    await callback.message.answer("🔍 Nessun profilo disponibile in questa città. Nuovi arrivi in arrivo, resta sintonizzato!")

@router.message(F.text == "/newprofile")
async def new_profile(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer("Solo gli amministratori possono aggiungere profili.")
        return
    await state.set_state(Profile.city)
    await message.answer("📍 Inserisci la città:")

@router.message(Profile.city)
async def profile_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(Profile.name)
    await message.answer("👤 Inserisci il nome:")

@router.message(Profile.name)
async def profile_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Profile.age)
    await message.answer("🎂 Inserisci l'età:")

@router.message(Profile.age)
async def profile_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(Profile.description)
    await message.answer("📝 Inserisci la descrizione:")

@router.message(Profile.description)
async def profile_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(Profile.photo)
    await message.answer("📸 Invia la foto:")

@router.message(Profile.photo, F.photo)
async def profile_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(Profile.whatsapp)
    await message.answer("📞 Inserisci il link WhatsApp (senza anteprima):")

@router.message(Profile.whatsapp)
async def profile_whatsapp(message: types.Message, state: FSMContext):
    data = await state.update_data(whatsapp=message.text)
    profile = await state.get_data()

    text = (
        f"<b>{profile['name']}, {profile['age']}</b>\n"
        f"{profile['description']}\n\n"
        f"<b>Città:</b> {profile['city']}\n"
        f"<b>WhatsApp:</b> <a href='{profile['whatsapp']}'>Contatto</a>"
    )

    await bot.send_photo(
        chat_id=message.chat.id,
        photo=profile['photo'],
        caption=text,
        reply_markup=vote_kb(profile_id="123"),  # позже подставим ID
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
