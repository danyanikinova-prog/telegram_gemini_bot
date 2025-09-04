import os
import asyncio
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiohttp import web

# --- Flask через aiohttp (совместимый с Render) ---
async def flask_app():
    app = Flask(__name__)

    @app.route("/health")
    def health():
        return "OK", 200

    port = int(os.getenv("PORT", 10000))
    return web._run_app(app, host="0.0.0.0", port=port)

# --- Telegram Bot ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
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

# --- Запуск Render-friendly ---
async def main():
    # запускаем бота и flask вместе
    bot_task = asyncio.create_task(dp.start_polling(bot))
    flask_task = asyncio.create_task(flask_app())
    await asyncio.gather(bot_task, flask_task)

if __name__ == "__main__":
    asyncio.run(main())
