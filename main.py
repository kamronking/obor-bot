import asyncio
import os
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, \
    InlineKeyboardButton
from dotenv import load_dotenv

# Загрузка токена и ID из .env файла
load_dotenv()
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()

# ID курьера (проверьте, что в .env стоит правильный ID)
COURIER_ID = int(os.getenv('COURIER_ID', 0))
WEB_APP_URL = "https://kamronking.github.io/obor-bot/"


@dp.message(F.text == "/start")
async def start(message: Message):
    # ВАЖНО: WebApp открывается именно через Reply-кнопку для работы sendData
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Заказать / Buyurtma", web_app=WebAppInfo(url=WEB_APP_URL))]
    ], resize_keyboard=True)

    await message.answer(
        "👋 <b>Obor Delivery</b>\n\nНажмите кнопку внизу для оформления заказа:",
        reply_markup=kb,
        parse_mode="HTML"
    )


@dp.message(F.web_app_data)
async def web_app_data_handler(message: Message):
    try:
        # Извлекаем JSON данные из WebApp
        data = json.loads(message.web_app_data.data)
        oid = str(int(datetime.now().timestamp()) % 1000)  # Генерация ID заказа

        is_uz = data.get('lang') == 'uz'
        confirm_msg = (f"✅ <b>Заказ №{oid} принят!</b>" if not is_uz
                       else f"✅ <b>Buyurtma №{oid} qabul qilindi!</b>")

        details = (f"📦 {data['what']} ({data.get('weight', '?')} кг)\n"
                   f"📍 Откуда: {data['from']}\n"
                   f"👤 {data['name']}\n"
                   f"📞 {data['phone']}")

        # Формирование локации
        if data.get('lat') and data.get('lat') != 0:
            loc_url = f"https://www.google.com/maps?q={data['lat']},{data['lon']}"
            loc_text = f"📍 <a href='{loc_url}'>ЛОКАЦИЯ НА КАРТЕ</a>"
        else:
            loc_text = "📍 Локация не указана"

        # 1. Ответ пользователю
        await message.answer(confirm_msg, parse_mode="HTML")

        # 2. Уведомление курьеру
        if COURIER_ID != 0:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🚕 Принять", callback_data=f"acc_{oid}")]
            ])
            await bot.send_message(
                COURIER_ID,
                f"🚚 <b>НОВЫЙ ЗАКАЗ #{oid}</b>\n\n{details}\n\n{loc_text}",
                reply_markup=kb,
                parse_mode="HTML",
                disable_web_page_preview=True
            )

        print(f"Заказ #{oid} успешно обработан.")

    except Exception as e:
        print(f"Ошибка при обработке данных WebApp: {e}")


async def main():
    print("🚀 Бот запущен и готов к работе!")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())