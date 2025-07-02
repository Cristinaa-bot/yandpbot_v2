import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    FSInputFile,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Router
import asyncio

# ======= CONFIG =======
API_TOKEN = "8146798235:AAG-JTJOjHaljEDGBs_hlMjMpVbyw6Ih1Qo"
ADMINS = [7457586608, 7273958700, 6774952360]
CITIES = ["Milano", "Roma", "Firenze"]
# ======================

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()


# ======= STATES =======
class ProfileForm(StatesGroup):
    text = State()
    photos = State()


# ======= KEYBOARDS =======
def cities_kb():
    buttons = [InlineKeyboardButton(text=city, callback_data=f"city:{city}") for city in CITIES]
    return InlineKeyboardMarkup(inline_keyboard=[[b] for b in buttons])


def vote_kb(profile_id: str):
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
async def handle_city(callback: types.CallbackQuery):
    await callback.message.answer("🔍 Nessun profilo disponibile in questa città. Nuovi arrivi in arrivo, resta sintonizzato!")


@router.message(F.text == "/newprofile")
async def cmd_newprofile(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    await state.set_state(ProfileForm.text)
    await message.answer("✍🏻 Invia 8 righe del profilo come un messaggio di testo (nome, età, città, ecc.)")


@router.message(ProfileForm.text, F.text)
async def get_text(message: Message, state: FSMContext):
    lines = message.text.strip().split("\n")
    if len(lines) < 8:
        await message.answer("❗️Per favore, invia esattamente 8 righe.")
        return
    await state.update_data(text=lines)
    await state.set_state(ProfileForm.photos)
    await message.answer("📸 Invia ora 5 foto come un solo album.")

@router.message(F.media_group_id)
async def handle_album(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # Проверка: пользователь должен быть в процессе создания анкеты
    profile = profiles.get(user_id)
    if not profile:
        return

    # Сохраняем фото в альбом
    album_buffer.setdefault(user_id, []).append(message.photo[-1].file_id)

    # Если получено 5 фото — сообщаем
    if len(album_buffer[user_id]) == 5:
        await message.answer("✅ Tutte le foto ricevute. Invia /done per pubblicare il profilo.")

# === Новый блок обработки фото и команды /done ===
from aiogram.types import FSInputFile

PHOTO_LIMIT = 5
photo_buffer = {}

@router.message(Profile.photo, F.photo)
async def handle_photos(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    photo_buffer.setdefault(user_id, [])
    photo_buffer[user_id].append(message.photo[-1].file_id)

    if len(photo_buffer[user_id]) < PHOTO_LIMIT:
        await message.answer(f"📸 {len(photo_buffer[user_id])}/5 foto ricevute. Invia le rimanenti.")
    elif len(photo_buffer[user_id]) == PHOTO_LIMIT:
        await state.set_state(Profile.whatsapp)
        await message.answer("📞 Inserisci il link WhatsApp (senza anteprima):")

@router.message(Profile.whatsapp)
async def handle_whatsapp(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.update_data(whatsapp=message.text)
    profile = await state.get_data()
    photos = photo_buffer.get(user_id, [])

    text = (
        f"<b>{profile['name']}, {profile['age']}</b>\n"
        f"{profile['description']}\n\n"
        f"<b>Città:</b> {profile['city']}\n"
        f"<b>WhatsApp:</b> <a href='{profile['whatsapp']}'>Contatto</a>"
    )

    # Отправить фото как альбом
    media_group = [types.InputMediaPhoto(media=photo_id) for photo_id in photos[:-1]]
    await bot.send_media_group(chat_id=message.chat.id, media=media_group)
    await bot.send_photo(
        chat_id=message.chat.id,
        photo=photos[-1],
        caption=text,
        reply_markup=vote_kb(profile_id="123"),  # здесь может быть ID профиля
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

    photo_buffer.pop(user_id, None)
    await state.clear()
    await message.answer("✅ Profilo pubblicato con successo!")

@router.message(F.text.startswith("/"))
async def unknown_command(message: Message):
    if message.from_user.id in ADMINS:
        await message.answer("Usa /newprofile per aggiungere un nuovo profilo.")
    else:
        await message.answer("Seleziona una città per vedere i profili disponibili.", reply_markup=cities_kb())

# ======= RUN =======
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
