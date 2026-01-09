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

COURIER_ID = int(os.getenv('COURIER_ID', 0))
WEB_APP_URL = "https://kamronking.github.io/obor-bot/"


@dp.message(F.text == "/start")
async def start(message: Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Заказать / Buyurtma", web_app=WebAppInfo(url=WEB_APP_URL))]
    ], resize_keyboard=True)
    await message.answer("👋 <b>Obor Delivery</b>\nНажмите кнопку для заказа:", reply_markup=kb, parse_mode="HTML")


# --- 1. ПРИЕМ ЗАКАЗА ИЗ WEB APP ---
@dp.message(F.web_app_data)
async def web_app_data_handler(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        oid = str(int(datetime.now().timestamp()) % 1000)
        user_id = message.from_user.id

        is_uz = data.get('lang') == 'uz'
        confirm_msg = f"✅ <b>Заказ №{oid} оформлен!</b>" if not is_uz else f"✅ <b>Buyurtma №{oid} qabul qilindi!</b>"

        details = (f"📦 {data['what']} ({data.get('weight', '?')} кг)\n"
                   f"📍 Откуда: {data['from']}\n"
                   f"👤 Клиент: {data['name']}\n"
                   f"📞 Тел: {data['phone']}")

        loc_text = "📍 Локация не указана"
        if data.get('lat') and data.get('lat') != 0:
            loc_url = f"https://www.google.com/maps?q={data['lat']},{data['lon']}"
            loc_text = f"📍 <a href='{loc_url}'>ЛОКАЦИЯ НА КАРТЕ</a>"

        await message.answer(confirm_msg, parse_mode="HTML")

        # Кнопка для курьера: Принять
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
        print(f"Ошибка WebApp: {e}")


# --- 2. ОБРАБОТКА "ПРИНЯТЬ ЗАКАЗ" ---
@dp.callback_query(F.data.startswith("acc_"))
async def accept_order(callback: CallbackQuery):
    parts = callback.data.split("_")
    order_id, client_id = parts[1], parts[2]

    await callback.answer("Заказ принят!")

    # Кнопка меняется на "Доставлено"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ ДОСТАВЛЕНО", callback_data=f"done_{order_id}_{client_id}")]
    ])

    new_text = callback.message.text + f"\n\nСтатус: 🚕 <b>В ПУТИ</b>"
    await callback.message.edit_text(new_text, parse_mode="HTML", reply_markup=kb)

    # Уведомляем клиента
    try:
        await bot.send_message(client_id, f"🚕 Курьер принял ваш заказ <b>№{order_id}</b> и уже выезжает!",
                               parse_mode="HTML")
    except:
        pass


# --- 3. ОБРАБОТКА "ДОСТАВЛЕНО" ---
@dp.callback_query(F.data.startswith("done_"))
async def finish_order(callback: CallbackQuery):
    parts = callback.data.split("_")
    order_id, client_id = parts[1], parts[2]

    await callback.answer("Заказ завершен!")

    # Убираем все кнопки, пишем финальный статус
    final_text = callback.message.text.replace("Статус: 🚕 <b>В ПУТИ</b>", "")
    final_text += f"\n\nСтатус: 🏁 <b>ДОСТАВЛЕН</b> ({datetime.now().strftime('%H:%M')})"

    await callback.message.edit_text(final_text, parse_mode="HTML", reply_markup=None)

    # Уведомляем клиента
    try:
        await bot.send_message(client_id,
                               f"✅ Ваш заказ <b>№{order_id}</b> успешно доставлен! Спасибо, что выбрали нас.",
                               parse_mode="HTML")
    except:
        pass


async def main():
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
