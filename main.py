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

# Хранилище принятых заказов
active_orders_lock = {}


@dp.message(Command("start"))
async def start(message: Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Заказать / Buyurtma berish",
                        web_app=WebAppInfo(url="https://kamronking.github.io/obor-bot/"))]
    ], resize_keyboard=True)
    await message.answer("🇷🇺 Сделайте заказ / 🇺🇿 Buyurtma bering", reply_markup=kb)


@dp.message(F.web_app_data)
async def handle_webapp(message: Message):
    data = json.loads(message.web_app_data.data)
    oid = f"{datetime.now().strftime('%H%M')}-{random.randint(10, 99)}"
    lang = data.get('lang', 'ru')

    # Текст заказа для курьера
    type_str = "📦 ПОСЫЛКА / POSILKA" if data['type'] == 'parcel' else "🛒 ПРОДУКТЫ / MAHSULOTLAR"
    details = f"📝 Что: {data['what']}\n👤 Клиент: {data['name']} ({data['phone']})"
    if data['type'] == 'parcel':
        details += f"\n👤 Кому: {data['rec_name']} ({data['rec_phone']})"

    loc_link = f"📍 <a href='https://www.google.com/maps?q={data['lat']},{data['lon']}'>КАРТА</a>" if data[
        'lat'] else "📍 Уточнить адрес"

    text_adm = f"🚚 <b>ЗАКАЗ #{oid}</b>\n━━━━━━━━━━━━━━━\n<b>{type_str}</b>\n{details}\n━━━━━━━━━━━━━━━\n{loc_link}"

    kb_adm = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🚕 ПРИНЯТЬ / QABUL QILISH",
                                                                         callback_data=f"acc_{oid}_{message.from_user.id}_{lang}")]])

    for aid in ADMIN_IDS:
        await bot.send_message(aid, text_adm, reply_markup=kb_adm, parse_mode="HTML", disable_web_page_preview=True)

    # Сообщение клиенту с кнопкой отмены
    resp = "✅ Отправлено!" if lang == 'ru' else "✅ Yuborildi!"
    kb_cancel = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ ОТМЕНИТЬ / BEKOR QILISH", callback_data=f"can_{oid}_{lang}")]])
    await message.answer(resp, reply_markup=kb_cancel)


@dp.callback_query(F.data.startswith("acc_"))
async def accept_order(callback: CallbackQuery):
    _, oid, uid, lang = callback.data.split("_")
    if oid in active_orders_lock:
        return await callback.answer("❌ Уже занято!", show_alert=True)

    active_orders_lock[oid] = callback.from_user.first_name
    kb_done = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏁 ДОСТАВИЛ / YETKAZDIM", callback_data=f"done_{oid}_{uid}_{lang}")]])

    await callback.message.edit_text(callback.message.html_text + f"\n\n🤝 <b>ВЗЯЛ: {callback.from_user.first_name}</b>",
                                     reply_markup=kb_done, parse_mode="HTML", disable_web_page_preview=True)
    await bot.send_message(uid, f"🚕 Курьер {callback.from_user.first_name} принял заказ!")


@dp.callback_query(F.data.startswith("can_"))
async def cancel_order(callback: CallbackQuery):
    _, oid, lang = callback.data.split("_")
    if oid in active_orders_lock:
        msg = "❌ Нельзя отменить! Курьер уже принял заказ." if lang == 'ru' else "❌ Bekor qilib bo'lmaydi! Kuryer qabul qildi."
        return await callback.answer(msg, show_alert=True)

    await callback.message.edit_text("❌ Заказ отменен / Buyurtma bekor qilindi")
    for aid in ADMIN_IDS:
        await bot.send_message(aid, f"🚫 Заказ #{oid} отменен клиентом.")


@dp.callback_query(F.data.startswith("done_"))
async def order_done(callback: CallbackQuery):
    _, oid, uid, lang = callback.data.split("_")
    await callback.message.edit_text(callback.message.html_text.replace("🤝", "✅") + "\n\n🏁 <b>ДОСТАВЛЕНО</b>",
                                     reply_markup=None, parse_mode="HTML")
    await bot.send_message(uid, "🏁 Доставлено! Спасибо.")


async def main(): await dp.start_polling(bot)


if __name__ == '__main__': asyncio.run(main())