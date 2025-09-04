from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import asyncio
import os

from google import genai
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

client = genai.Client(api_key=GOOGLE_API_KEY)

# --- Состояния ---
class AnimatePhoto(StatesGroup):
    waiting_photo = State()
    waiting_confirm = State()

# --- Простая "база балансов" (для примера) ---
user_balances = {}

def get_balance(user_id):
    return user_balances.get(user_id, 100)  # стартово 100 ₽ для теста

def update_balance(user_id, amount):
    user_balances[user_id] = get_balance(user_id) + amount

# --- Главное меню ---
def main_menu():
    kb = [
        [InlineKeyboardButton(text="🖼 Анимировать фотографию", callback_data="animate")],
        [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="topup")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- /start ---
@dp.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer(
        "👋 Привет! Этот бот оживит любую фотографию.\n"
        "Стоимость анимации — 35 ₽.\n\n"
        "Выберите действие:",
        reply_markup=main_menu()
    )

# --- Кнопки ---
@dp.callback_query()
async def callbacks(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    if callback.data == "animate":
        await callback.message.answer("📷 Загрузите фотографию (только одну).")
        await state.set_state(AnimatePhoto.waiting_photo)

    elif callback.data == "topup":
        await callback.message.answer("💳 Пополнение баланса временно доступно только вручную. (заглушка)")

    elif callback.data == "start_animation":
        balance = get_balance(user_id)
        if balance < 35:
            await callback.message.answer("⚠ Недостаточно средств. Нужно 35 ₽.", 
                                          reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                              [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="topup")]
                                          ]))
        else:
            await callback.message.answer("⏳ Запускаю анимацию, подождите...")
            data = await state.get_data()
            photo_url = data.get("photo_url")

            # Генерация видео
            try:
                video_url = generate_video_from_photo(photo_url, "Анимируй фотографию красиво")
                update_balance(user_id, -35)
                await callback.message.answer_video(video_url, caption="✅ Готово! 35 ₽ списано.")
            except Exception as e:
                await callback.message.answer(f"❌ Ошибка генерации: {e}")

            await state.clear()

# --- Обработка фото ---
@dp.message(StateFilter(AnimatePhoto.waiting_photo))
async def handle_photo(message: Message, state: FSMContext):
    user_id = message.from_user.id
    file = await bot.get_file(message.photo[-1].file_id)
    photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
    await state.update_data(photo_url=photo_url)

    balance = get_balance(user_id)
    if balance < 35:
        await message.answer("⚠ Недостаточно средств для анимации.", 
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                 [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="topup")]
                             ]))
        await state.clear()
    else:
        await message.answer("Фото получено ✅\nНажмите ▶ Начать анимацию", 
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                 [InlineKeyboardButton(text="▶ Начать анимацию", callback_data="start_animation")]
                             ]))
        await state.set_state(AnimatePhoto.waiting_confirm)

# --- Функция генерации через Veo ---
def generate_video_from_photo(photo_url, description):
    response = client.models.generate_content(
        model="veo-2",
        contents=[
            {"role": "user", "parts": [
                {"text": description},
                {"file_data": {"mime_type": "image/jpeg", "file_uri": photo_url}}
            ]}
        ],
        config={
            "video_config": {"duration_seconds": 5, "fps": 24}
        }
    )

    operation_id = response.operation.name
    while True:
        op = client.operations.get(name=operation_id)
        if op.done:
            break
        time.sleep(5)

    return op.response["video"]["uri"]

# --- Запуск ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
