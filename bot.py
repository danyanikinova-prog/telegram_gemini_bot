import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from dotenv import load_dotenv
from google import genai

# Загружаем ключи
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Настраиваем бота и Gemini
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = genai.Client(api_key=GOOGLE_API_KEY)

@dp.message()
async def handle_msg(message: Message):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=message.text
    )
    answer = response.text if response.text else "Ошибка при запросе к Gemini"
    await message.answer(answer)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
