import asyncio
import os
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv

load_dotenv()
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()

# ID курьера из .env
COURIER_ID = int(os.getenv('COURIER_ID', 0))
WEB_APP_URL = "https://kamronking.github.io/obor-bot/"

@dp.message(F.text == "/start")
async def start(message: Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Заказать / Buyurtma", web_app=WebAppInfo(url=WEB_APP_URL))]
    ], resize_keyboard=True)
    await message.answer("👋 <b>Obor Delivery</b>\nНажмите кнопку для заказа:", reply_markup=kb, parse_mode="HTML")

# --- ОБРАБОТКА ДАННЫХ ИЗ WEB APP ---
@dp.message(F.web_app_data)
async def web_app_data_handler(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        oid = str(int(datetime.now().timestamp()) % 1000)
        user_id = message.from_user.id
        user_name = message.from_user.full_name

        is_uz = data.get('lang') == 'uz'
        confirm_msg = f"✅ <b>Заказ №{oid} оформлен!</b>" if not is_uz else f"✅ <b>Buyurtma №{oid} qabul qilindi!</b>"

        details = (f"📦 {data['what']} ({data.get('weight', '?')} кг)\n"
                   f"📍 Откуда: {data['from']}\n"
                   f"👤 Клиент: {data['name']}\n"
                   f"📞 Тел: {data['phone']}")

        if data.get('lat') and data.get('lat') != 0:
            loc_url = f"https://www.google.com/maps?q={data['lat']},{data['lon']}"
            loc_text = f"📍 <a href='{loc_url}'>ЛОКАЦИЯ НА КАРТЕ</a>"
        else:
            loc_text = "📍 Локация не указана"

        await message.answer(confirm_msg, parse_mode="HTML")

        # Кнопка для курьера с вшитым ID заказа и ID клиента
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚕 ПРИНЯТЬ ЗАКАЗ", callback_data=f"acc_{oid}_{user_id}")]
        ])

        await bot.send_message(
            COURIER_ID,
            f"🚚 <b>НОВЫЙ ЗАКАЗ #{oid}</b>\n\n{details}\n\n{loc_text}",
            reply_markup=kb,
            parse_mode="HTML",
            disable_web_page_preview=False
        )
    except Exception as e:
        print(f"Ошибка в WebAppData: {e}")

# --- ОБРАБОТКА НАЖАТИЯ КНОПКИ КУРЬЕРОМ ---
@dp.callback_query(F.data.startswith("acc_"))
async def accept_order(callback: CallbackQuery):
    try:
        # Разбираем callback_data (acc_IDзаказа_IDклиента)
        parts = callback.data.split("_")
        order_id = parts[1]
        client_id = parts[2]

        # 1. Отвечаем Telegram, чтобы убрать "загрузку" на кнопке
        await callback.answer("Вы приняли заказ!")

        # 2. Изменяем сообщение у курьера (убираем кнопку)
        new_text = callback.message.text + f"\n\n✅ <b>ПРИНЯТ: {datetime.now().strftime('%H:%M')}</b>"
        await callback.message.edit_text(new_text, parse_mode="HTML", reply_markup=None)

        # 3. Уведомляем клиента, что курьер принял заказ
        await bot.send_message(
            client_id,
            f"🚕 Курьер принял ваш заказ <b>№{order_id}</b> и уже выезжает!",
            parse_mode="HTML"
        )

    except Exception as e:
        print(f"Ошибка при нажатии кнопки: {e}")
        await callback.answer("Произошла ошибка при принятии заказа.", show_alert=True)

async def main():
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())