import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import Router
import asyncio

API_TOKEN = "8146798235:AAG-JTJOjHaljEDGBs_hlMjMpVbyw6Ih1Qo"
ADMINS = [7457586608, 7273958700, 6774952360]

CITIES = ["Milano", "Roma", "Firenze"]

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

class Profile(StatesGroup):
    text = State()
    photos = State()

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

@router.message(F.text == "/start")
async def cmd_start(message: types.Message):
    await message.answer("Benvenuto! Seleziona la città per vedere i profili disponibili:", reply_markup=cities_kb())

@router.callback_query(F.data.startswith("city:"))
async def handle_city_selection(callback: types.CallbackQuery):
    await callback.message.answer("🔍 Nessun profilo disponibile in questa città. Nuovi arrivi in arrivo, resta sintonizzato!")

@router.message(F.text == "/newprofile")
async def new_profile(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    await state.set_state(Profile.text)
    await message.answer("📋 Invia le 8 righe di testo per il profilo:")

@router.message(Profile.text)
async def handle_text(message: types.Message, state: FSMContext):
    lines = message.text.strip().split("\n")
    if len(lines) != 8:
        await message.answer("❌ Devi inviare esattamente 8 righe di testo.")
        return
    await state.update_data(
        name=lines[0],
        age=lines[1],
        city=lines[2],
        nationality=lines[3],
        dates=lines[4],
        availability=lines[5],
        preferences=lines[6],
        whatsapp=lines[7],
        photos=[]
    )
    await state.set_state(Profile.photos)
    await message.answer("📸 Invia 5 foto (tutte insieme, come album).")

@router.message(Profile.photos, F.media_group_id)
async def handle_album(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)

@router.message(Profile.photos, F.text == "/done")
async def handle_done(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    data = await state.get_data()
    photos = data.get("photos", [])
    if len(photos) < 5:
        await message.answer("❌ Devi inviare almeno 5 foto.")
        return

    text = (
        f"<b>{data['name']}, {data['age']}</b>\n"
        f"<b>{data['nationality']}</b>\n"
        f"{data['preferences']}\n\n"
        f"<b>📍 {data['city']}</b>\n"
        f"📅 {data['dates']}\n"
        f"🕓 {data['availability']}\n"
        f"<b>WhatsApp:</b> <a href='https://wa.me/{data['whatsapp'].replace('+', '').replace(' ', '')}'>Contatto</a>"
    )

    for photo_id in photos:
        await bot.send_photo(message.chat.id, photo=photo_id)

    await bot.send_message(message.chat.id, text, reply_markup=vote_kb("123"), disable_web_page_preview=True)
    await message.answer("✅ Profilo pubblicato con successo!")
    await state.clear()

@router.message(F.text == "/done")
async def done_wrong_state(message: types.Message):
    await message.answer("❌ Nessun profilo in corso. Usa /newprofile per iniziare.")

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
