import asyncio
import os
import json
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
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
# ССЫЛКА НА ТВОЙ ПРОФИЛЬ (Замени на свой ник без @)
SUPPORT_URL = "https://t.me/obor_bot_support"

# Настройка Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client_sheet = gspread.authorize(creds)
sheet = client_sheet.open("Obor-bot-orders").worksheet("Orders")

active_orders_lock = {}
cancelled_orders = set()


def save_to_sheets(order_id, data):
    try:
        now = datetime.now().strftime('%d.%m %H:%M')
        row = [order_id, now, data.get('name'), data.get('phone'), data.get('what'), "🆕 НОВЫЙ",
               f"{data.get('lat')}, {data.get('lon')}" if data.get('lat') else "Посылка"]
        sheet.append_row(row)
    except Exception as e:
        print(f"Ошибка записи: {e}")


def update_sheet_status(order_id, new_status):
    try:
        cell = sheet.find(order_id)
        if cell: sheet.update_cell(cell.row, 6, new_status)
    except Exception as e:
        print(f"Ошибка обновления: {e}")


@dp.message(Command("start"))
async def start(message: Message):
    # ДОБАВИЛИ КНОПКУ ПОДДЕРЖКИ В МЕНЮ
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Заказать / Buyurtma berish",
                        web_app=WebAppInfo(url="https://kamronking.github.io/obor-bot/"))],
        [KeyboardButton(text="🆘 Поддержка / Support")]
    ], resize_keyboard=True)
    await message.answer("🇷🇺 Сделайте заказ или напишите нам.\n🇺🇿 Buyurtma bering yoki bizga yozing.", reply_markup=kb)


# ОБРАБОТКА КНОПКИ ПОДДЕРЖКИ
@dp.message(F.text.contains("Поддержка") | F.text.contains("Support"))
async def support_handler(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💻 Написать админу / Admin bilan bog'lanish", url=SUPPORT_URL)]
    ])
    await message.answer(
        "🇷🇺 Нажмите кнопку ниже, чтобы написать администратору:\n🇺🇿 Admin bilan bog'lanish uchun pastdagi tugmani bosing:",
        reply_markup=kb)


@dp.message(F.web_app_data)
async def handle_webapp(message: Message):
    data = json.loads(message.web_app_data.data)
    oid = f"{datetime.now().strftime('%H%M')}-{random.randint(10, 99)}"
    lang = data.get('lang', 'ru')
    save_to_sheets(oid, data)

    type_str = "📦 ПОСЫЛКА / POSILKA" if data['type'] == 'parcel' else "🛒 ПРОДУКТЫ / MAHSULOTLAR"
    details = f"📝 Что: {data['what']}\n👤 Клиент: {data['name']} ({data['phone']})"
    if data['type'] == 'parcel': details += f"\n👤 Кому: {data['rec_name']} ({data['rec_phone']})"

    loc_link = f"📍 <a href='http://maps.google.com/maps?q={data['lat']},{data['lon']}'>КАРТА</a>" if data[
        'lat'] else "📍 Уточнить адрес"
    text_adm = f"🚚 <b>ЗАКАЗ #{oid}</b>\n━━━━━━━━━━━━━━━\n<b>{type_str}</b>\n{details}\n━━━━━━━━━━━━━━━\n{loc_link}"

    kb_adm = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🚕 ПРИНЯТЬ / QABUL QILISH",
                                                                         callback_data=f"acc_{oid}_{message.from_user.id}_{lang}")]])
    for aid in ADMIN_IDS:
        await bot.send_message(aid, text_adm, reply_markup=kb_adm, parse_mode="HTML", disable_web_page_preview=True)

    # ДОБАВИЛИ КНОПКУ ПОДДЕРЖКИ И СЮДА ТОЖЕ
    kb_cancel = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ ОТМЕНИТЬ / BEKOR QILISH", callback_data=f"can_{oid}_{lang}")],
        [InlineKeyboardButton(text="🆘 Поддержка / Support", url=SUPPORT_URL)]
    ])
    await message.answer("✅ Отправлено!" if lang == 'ru' else "✅ Yuborildi!", reply_markup=kb_cancel)


@dp.callback_query(F.data.startswith("acc_"))
async def accept_order(callback: CallbackQuery):
    _, oid, uid, lang = callback.data.split("_")
    if oid in cancelled_orders:
        await callback.message.edit_text(callback.message.html_text + f"\n\n🚫 <b>ОТМЕНЕНО КЛИЕНТОМ</b>",
                                         reply_markup=None)
        return await callback.answer("Заказ уже отменен!", show_alert=True)
    if oid in active_orders_lock:
        return await callback.answer("Уже занято!", show_alert=True)

    active_orders_lock[oid] = callback.from_user.first_name
    update_sheet_status(oid, f"🚕 В ПУТИ ({callback.from_user.first_name})")
    kb_done = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏁 ДОСТАВИЛ / YETKAZDIM", callback_data=f"done_{oid}_{uid}_{lang}")]])
    await callback.message.edit_text(callback.message.html_text + f"\n\n🤝 <b>ВЗЯЛ: {callback.from_user.first_name}</b>",
                                     reply_markup=kb_done, parse_mode="HTML", disable_web_page_preview=True)
    await bot.send_message(uid, f"🚕 Курьер {callback.from_user.first_name} принял заказ!")


@dp.callback_query(F.data.startswith("can_"))
async def cancel_order(callback: CallbackQuery):
    _, oid, lang = callback.data.split("_")
    if oid in active_orders_lock:
        return await callback.answer("Нельзя отменить! Курьер уже в пути.", show_alert=True)
    cancelled_orders.add(oid)
    update_sheet_status(oid, "❌ ОТМЕНЕН КЛИЕНТОМ")
    await callback.message.edit_text("❌ Заказ отменен / Buyurtma bekor qilindi")
    for aid in ADMIN_IDS: await bot.send_message(aid, f"🚫 Заказ #{oid} отменен клиентом.")


@dp.callback_query(F.data.startswith("done_"))
async def order_done(callback: CallbackQuery):
    _, oid, uid, lang = callback.data.split("_")
    update_sheet_status(oid, "🏁 ДОСТАВЛЕН")
    await callback.message.edit_text(callback.message.html_text.replace("🤝", "✅") + "\n\n🏁 <b>ДОСТАВЛЕНО</b>",
                                     reply_markup=None, parse_mode="HTML")
    await bot.send_message(uid, "🏁 Доставлено! Спасибо.")


async def main(): await dp.start_polling(bot)


if __name__ == '__main__': asyncio.run(main())