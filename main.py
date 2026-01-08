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
WEB_APP_URL = "https://kamronking.github.io/obor-bot/"


@dp.message(F.text == "/start")
async def start(message: Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Заказать / Buyurtma", web_app=WebAppInfo(url=WEB_APP_URL))]
    ], resize_keyboard=True)
    await message.answer("👋 <b>Obor Delivery</b>\n\nНажмите кнопку для заказа:\nBuyurtma berish uchun tugmani bosing:",
                         reply_markup=kb, parse_mode="HTML")


@dp.message(F.web_app_data)
async def web_app_data_handler(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        oid = str(int(datetime.now().timestamp()) % 1000)

        details = f"📦 {data['what']} ({data['weight']})\n📍 Откуда: {data['from']}\n👤 {data['name']}\n📞 {data['phone']}"
        loc_url = f"https://www.google.com/maps?q={data['lat']},{data['lon']}"

        # Google Sheets
        append_order({
            "order_id": oid,
            "time": datetime.now().strftime("%H:%M"),
            "first_name": data['name'],
            "phone": data['phone'],
            "items": f"{data['what']} (из {data['from']})",
            "status": "🆕 НОВЫЙ"
        })

        await message.answer(f"✅ <b>Заказ №{oid} оформлен!</b>\nСкоро курьер свяжется с вами.", parse_mode="HTML")

        # Курьеру
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚕 Принять заказ", callback_data=f"acc_{oid}_{message.from_user.id}")]
        ])
        await bot.send_message(
            COURIER_ID,
            f"🚚 <b>НОВЫЙ ЗАКАЗ #{oid}</b>\n\n{details}\n\n📍 <a href='{loc_url}'>ЛОКАЦИЯ НА КАРТЕ</a>",
            reply_markup=kb,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except Exception as e:
        print(f"Error processing web_app_data: {e}")


@dp.callback_query(F.data.startswith("acc_"))
async def accept_handler(callback: CallbackQuery):
    _, oid, uid = callback.data.split("_")
    update_order_status(oid, "🚕 В ПУТИ")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏁 Завершить", callback_data=f"done_{oid}_{uid}")]
    ])
    await callback.message.edit_text(callback.message.text + "\n\n✅ <b>Вы приняли этот заказ</b>", reply_markup=kb)
    await bot.send_message(uid, f"🚕 Курьер принял ваш заказ <b>#{oid}</b> и уже в пути!")


@dp.callback_query(F.data.startswith("done_"))
async def done_handler(callback: CallbackQuery):
    _, oid, uid = callback.data.split("_")
    update_order_status(oid, "🏁 ЗАВЕРШЕН")
    await callback.message.edit_text(callback.message.text + "\n\n🏁 <b>ЗАКАЗ ВЫПОЛНЕН</b>", reply_markup=None)
    await bot.send_message(uid, f"🏁 Ваш заказ <b>#{oid}</b> успешно доставлен!")


async def main():
    print("✅ Бот запущен и готов к работе!")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())