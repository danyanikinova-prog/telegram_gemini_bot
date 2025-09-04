import os
import base64
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from flask import Flask
from threading import Thread
from google import genai

# --- Настройки ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
GENAI_KEY = os.getenv("GENAI_API_KEY")

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
client = genai.Client(api_key=GENAI_KEY)

# Простая «база балансов»
user_balance = {}

# --- Клавиатуры ---
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎬 Анимировать фотографию")],
        [KeyboardButton(text="💰 Пополнить баланс")],
    ],
    resize_keyboard=True
)

start_anim_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 Начать анимацию")],
        [KeyboardButton(text="💰 Пополнить баланс")],
    ],
    resize_keyboard=True
)

# --- Хэндлеры ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user_balance[message.from_user.id] = user_balance.get(message.from_user.id, 35)  # стартовый баланс
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я — бот, который оживит твою фотографию 📸✨\n\n"
        "Стоимость анимации: <b>35 рублей</b>.",
        reply_markup=main_kb
    )

@dp.message(F.text == "🎬 Анимировать фотографию")
async def ask_photo(message: types.Message):
    await message.answer("📷 Загрузите одну фотографию для анимации.")

@dp.message(F.photo)
async def handle_photo(message: types.Message, state=None):
    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    photo_bytes = await bot.download_file(file_path)
    # сохраняем фото в память пользователя
    message.bot["last_photo"] = photo_bytes.read()
    await message.answer("✅ Фото получено.\nТеперь нажмите «🚀 Начать анимацию».", reply_markup=start_anim_kb)

@dp.message(F.text == "🚀 Начать анимацию")
async def animate_photo(message: types.Message):
    uid = message.from_user.id
    if user_balance.get(uid, 0) < 35:
        await message.answer("❌ Недостаточно средств. Пополните баланс.", reply_markup=main_kb)
        return

    photo_bytes = message.bot.get("last_photo")
    if not photo_bytes:
        await message.answer("⚠️ Сначала загрузите фотографию!")
        return

    await message.answer("⏳ Генерирую анимацию, подождите...")

    try:
        # Отправляем фото + текст в Gemini
        resp = client.models.generate_content(
            model="gemini-1.5-pro",
            contents=[{
                "role": "user",
                "parts": [
                    {"mime_type": "image/jpeg", "data": photo_bytes},
                    {"text": "Сделай анимацию этой фотографии. Короткое видео 5 секунд."}
                ]
            }],
            generation_config={"response_mime_type": "video/mp4"}
        )

        video_b64 = resp.candidates[0].content.parts[0].data
        video_bytes = base64.b64decode(video_b64)

        # списываем деньги
        user_balance[uid] -= 35

        await message.answer_video(video_bytes, caption="✨ Готово! Вот твоя анимация.")
    except Exception as e:
        await message.answer(f"❌ Ошибка генерации: {e}")

# --- Flask «пинг» ---
app = Flask(__name__)

@app.route("/")
def home():
    return "Бот работает!"

def run_flask():
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# --- Запуск ---
if __name__ == "__main__":
    # Flask в отдельном потоке
    Thread(target=run_flask).start()
    # aiogram
    asyncio.run(dp.start_polling(bot))
