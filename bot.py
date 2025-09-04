import os
import threading
import asyncio
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

# --- Flask для Render ---
app = Flask(__name__)

@app.route("/health")
def health():
    return "OK", 200

# --- Telegram Bot ---
BOT_TOKEN = os.getenv("BOT_TOKEN")  # не забудь задать переменную окружения BOT_TOKEN на Render
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    text = (
        "👋 Привет!\n\n"
        "Я бот, который оживляет фотографии.\n"
        "Стоимость анимации: 35 рублей.\n\n"
        "Выберите действие ниже 👇"
    )
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🎞 Анимировать фотографию")],
            [types.KeyboardButton(text="💳 Пополнить баланс")]
        ],
        resize_keyboard=True
    )
    await message.answer(text, reply_markup=keyboard)

# --- Функция запуска ---
async def run_bot():
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    port = int(os.getenv("PORT", 10000))  # Render отдаёт порт через переменную окружения
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port)).start()

    # Запускаем Telegram-бота
    asyncio.run(run_bot())
