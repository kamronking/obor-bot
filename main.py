import asyncio
import os
import json
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv()
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]

# Словарь для блокировки заказов (чтобы один заказ не взяли двое)
active_orders_lock = {}


@dp.message(Command("start"))
async def start(message: Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Заказать / Buyurtma berish",
                        web_app=WebAppInfo(url="https://kamronking.github.io/obor-bot/"))]
    ], resize_keyboard=True)
    await message.answer("🇷🇺 Сделайте заказ через приложение.\n🇺🇿 Ilova orqali buyurtma bering.", reply_markup=kb)


@dp.message(F.web_app_data)
async def handle_webapp(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        oid = f"{datetime.now().strftime('%H%M')}-{random.randint(10, 99)}"
        lang = data.get('lang', 'ru')

        # Логика формирования текста (RU + UZ)
        if data['type'] == 'parcel':
            type_str = "📦 ПОСЫЛКА / POSILKA"
            details = (f"📝 Что: {data['what']}\n"
                       f"👤 От/Kimdan: {data['name']} ({data['phone']})\n"
                       f"👤 Кому/Kimga: {data['rec_name']} ({data['rec_phone']})")
            loc_info = "📍 Адрес уточнить по телефону / Manzilni telefonda aniqlang"
        else:
            type_str = "🛒 ПРОДУКТЫ / MAHSULOTLAR"
            details = (f"📝 Список/Ro'yxat: {data['what']}\n"
                       f"👤 Клиент/Mijoz: {data['name']} ({data['phone']})")
            url = f"http://maps.google.com/maps?q={data['lat']},{data['lon']}"
            loc_info = f"📍 <a href='{url}'>ОТКРЫТЬ КАРТУ / MANZILNI KO'RISH</a>"

        text_adm = (f"🚚 <b>ЗАКАЗ / BUYURTMA #{oid}</b>\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"<b>{type_str}</b>\n"
                    f"{details}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"{loc_info}")

        # Кнопка для курьера на двух языках
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚕 ПРИНЯТЬ / QABUL QILISH",
                                  callback_data=f"acc_{oid}_{message.from_user.id}_{lang}")]
        ])

        for aid in ADMIN_IDS:
            await bot.send_message(aid, text_adm, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)

        resp = "✅ Отправлено! Курьер свяжется." if lang == 'ru' else "✅ Yuborildi! Kuryer bog'lanadi."
        await message.answer(resp)
    except Exception as e:
        print(f"Error: {e}")


@dp.callback_query(F.data.startswith("acc_"))
async def accept_order(callback: CallbackQuery):
    _, oid, uid, lang = callback.data.split("_")

    if oid in active_orders_lock:
        already_taken = active_orders_lock[oid]
        msg = f"❌ Заказ #{oid} уже взял {already_taken}!"
        return await callback.answer(msg, show_alert=True)

    active_orders_lock[oid] = callback.from_user.first_name

    # Кнопка "ДОСТАВИЛ" после принятия заказа
    kb_done = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏁 ДОСТАВИЛ / YETKAZDIM",
                              callback_data=f"done_{oid}_{uid}_{lang}")]
    ])

    new_text = callback.message.html_text + f"\n\n🤝 <b>ВЗЯЛ / OLDI: {callback.from_user.first_name}</b>"
    await callback.message.edit_text(new_text, reply_markup=kb_done, parse_mode="HTML", disable_web_page_preview=True)

    # Уведомление клиенту
    msg_client = f"🚕 Курьер {callback.from_user.first_name} принял ваш заказ!" if lang == 'ru' else f"🚕 Kuryer {callback.from_user.first_name} buyurtmangizni qabul qildi!"
    try:
        await bot.send_message(uid, msg_client)
    except:
        pass

    await callback.answer("Вы приняли заказ! / Buyurtmani oldingiz!")


@dp.callback_query(F.data.startswith("done_"))
async def order_done(callback: CallbackQuery):
    _, oid, uid, lang = callback.data.split("_")

    final_text = callback.message.html_text.replace("🤝", "✅") + "\n\n🏁 <b>СТАТУС: ДОСТАВЛЕНО / YETKAZILDI</b>"
    await callback.message.edit_text(final_text, reply_markup=None, parse_mode="HTML")

    msg_client = "🏁 Ваш заказ доставлен! Спасибо." if lang == 'ru' else "🏁 Buyurtmangiz yetkazildi! Rahmat."
    try:
        await bot.send_message(uid, msg_client)
    except:
        pass

    await callback.answer("Завершено! / Tayyor!")


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
