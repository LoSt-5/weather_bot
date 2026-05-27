import os
import logging
from html import escape
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import aiohttp

# Загружаем переменные окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

# Инициализируем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Отправь мне свою геолокацию или напиши название города, района или адреса, "
        "и я скажу текущую погоду в этом месте."
    )

# Обработчик геолокации
@dp.message(lambda message: message.location is not None)
async def handle_location(message: types.Message):
    lat = message.location.latitude
    lon = message.location.longitude
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    url = "http://api.weatherapi.com/v1/current.json"
    params = {
        "key": WEATHER_API_KEY,
        "q": f"{lat},{lon}",
        "lang": "ru"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    await send_weather_info(message, data)
                else:
                    await message.answer("❌ Не удалось получить данные о погоде. Попробуйте позже.")
        except Exception as e:
            logging.error(f"Ошибка при запросе к API: {e}")
            await message.answer("⚠️ Произошла ошибка при обращении к сервису погоды.")

# Обработчик текстовых сообщений (названия городов, адресов)
@dp.message(F.text)
async def handle_text(message: types.Message):
    query = message.text.strip()
    # Игнорируем команды (начинающиеся с '/'), чтобы не слать их как запрос погоды
    if not query or query.startswith('/'):
        return

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    url = "http://api.weatherapi.com/v1/current.json"
    params = {
        "key": WEATHER_API_KEY,
        "q": query,
        "lang": "ru"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    await send_weather_info(message, data)
                else:
                    # Пытаемся извлечь сообщение об ошибке из API
                    try:
                        error_data = await resp.json()
                        error_msg = error_data.get("error", {}).get("message", "Неизвестная ошибка")
                    except Exception:
                        error_msg = "Не удалось получить данные"
                    await message.answer(f"❌ {error_msg}")
        except Exception as e:
            logging.error(f"Ошибка при запросе к API: {e}")
            await message.answer("⚠️ Произошла ошибка при обращении к сервису погоды.")

async def send_weather_info(message: types.Message, data: dict):
    """Формирует и отправляет сообщение с погодой."""
    try:
        location = escape(data["location"]["name"])
        country = escape(data["location"]["country"])
        temp_c = data["current"]["temp_c"]
        condition = escape(data["current"]["condition"]["text"])
        feelslike_c = data["current"]["feelslike_c"]
        humidity = data["current"]["humidity"]
        wind_kph = data["current"]["wind_kph"]
        wind_dir = escape(data["current"]["wind_dir"])
        last_updated = escape(data["current"]["last_updated"])

        text = (
            f"🌍 <b>{location}, {country}</b>\n"
            f"🌡 Температура: {temp_c}°C (ощущается как {feelslike_c}°C)\n"
            f"☁️ {condition}\n"
            f"💧 Влажность: {humidity}%\n"
            f"💨 Ветер: {wind_kph} км/ч, направление {wind_dir}\n"
            f"🕒 Обновлено: {last_updated}"
        )
        await message.answer(text, parse_mode="HTML")
    except KeyError as e:
        logging.error(f"Ошибка парсинга ответа: {e}")
        await message.answer("⚠️ Не удалось обработать данные о погоде.")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())