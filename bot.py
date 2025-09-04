import os
import asyncio
import threading
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import CommandStart

# --- Telegram Bot ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer(
        "👋 Привет! Я Telegram-бот, который оживляет фотографии.\n\n"
        "Стоимость оживления одной фотографии — 35₽.\n\n"
        "Выберите действие:"
    )

# --- Flask-заглушка для Render ---
app = Flask(__name__)

@app.route("/")
def index():
    return "✅ Bot is running on Render!"

@app.route("/health")
def health():
    return "ok", 200

# --- Запуск ---
async def run_bot():
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000)).start()

    # Запускаем Telegram-бота
    asyncio.run(run_bot())
