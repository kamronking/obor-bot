import asyncio, os, json
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv
from google_sheets import append_order, update_order_status

load_dotenv()
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()
COURIER_ID = int(os.getenv('COURIER_ID', 0))
WEB_APP_URL = "https://kamronking.github.io/obor-bot/"  # ТВОЯ ССЫЛКА


@dp.message(F.text == "/start")
async def start(message: Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Заказать / Buyurtma", web_app=WebAppInfo(url=WEB_APP_URL))]
    ], resize_keyboard=True)
    await message.answer("Привет! Нажми на кнопку для заказа:", reply_markup=kb)


@dp.message(F.web_app_data)
async def web_app(message: Message):
    data = json.loads(message.web_app_data.data)
    oid = str(int(datetime.now().timestamp()) % 1000)

    # Формируем текст
    text = f"📦 {data['what']}\n📍 Откуда: {data['from']}\n⚖️ Вес: {data['weight']}\n👤 {data['name']}\n📞 {data['phone']}"
    loc_url = f"https://www.google.com/maps?q={data['lat']},{data['lon']}" if data['lat'] != 0 else "Не отправлена"

    # В таблицу
    append_order(
        {"order_id": oid, "time": datetime.now().strftime("%H:%M"), "first_name": data['name'], "phone": data['phone'],
         "items": text, "status": "🆕 НОВЫЙ"})

    await message.answer(f"✅ Заказ #{oid} принят!")

    # Курьеру
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅ Взять", callback_data=f"accept_{oid}_{message.from_user.id}")]])
    await bot.send_message(COURIER_ID, f"🚚 <b>ЗАКАЗ #{oid}</b>\n\n{text}\n📍 <a href='{loc_url}'>ЛОКАЦИЯ</a>",
                           reply_markup=kb, parse_mode="HTML")


# --- Сюда добавь функции accept_ и done_ из прошлого кода ---

async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())