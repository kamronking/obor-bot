import asyncio
import os
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()

# ID курьера (возьмите из @userinfobot)
COURIER_ID = int(os.getenv('COURIER_ID', 0))
# Ссылка на ваш GitHub Pages
WEB_APP_URL = "https://kamronking.github.io/obor-bot/"

@dp.message(F.text == "/start")
async def start(message: Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Заказать / Buyurtma", web_app=WebAppInfo(url=WEB_APP_URL))]
    ], resize_keyboard=True)
    await message.answer(
        "👋 <b>Obor Delivery</b>\n\nНажмите кнопку для заказа:\nBuyurtma berish uchun tugmani bosing:",
        reply_markup=kb,
        parse_mode="HTML"
    )

@dp.message(F.web_app_data)
async def web_app_data_handler(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        oid = str(int(datetime.now().timestamp()) % 1000) # Короткий ID заказа

        is_uz = data.get('lang') == 'uz'
        confirm_msg = (f"✅ <b>Заказ №{oid} оформлен!</b>\nСкоро курьер свяжется с вами."
                       if not is_uz else
                       f"✅ <b>Buyurtma №{oid} qabul qilindi!</b>\nKuryer siz bilan bog'lanadi.")

        details = (f"📦 {data['what']} ({data.get('weight', '?')} кг)\n"
                   f"📍 Откуда: {data['from']}\n"
                   f"👤 {data['name']}\n"
                   f"📞 {data['phone']}")

        # Ссылка на карту
        if data.get('lat') and data.get('lat') != 0:
            loc_url = f"https://www.google.com/maps?q={data['lat']},{data['lon']}"
            loc_text = f"📍 <a href='{loc_url}'>ЛОКАЦИЯ НА КАРТЕ</a>"
        else:
            loc_text = "📍 Локация не указана"

        await message.answer(confirm_msg, parse_mode="HTML")

        # Кнопка для курьера
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚕 Принять заказ", callback_data=f"acc_{oid}_{message.from_user.id}")]
        ])

        await bot.send_message(
            COURIER_ID,
            f"🚚 <b>НОВЫЙ ЗАКАЗ #{oid}</b>\n\n{details}\n\n{loc_text}",
            reply_markup=kb,
            parse_mode="HTML",
            disable_web_page_preview=False
        )
    except Exception as e:
        print(f"Ошибка: {e}")

async def main():
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
