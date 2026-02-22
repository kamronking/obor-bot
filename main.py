import asyncio
import os
import json
import random
import gspread
import time
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
WEB_APP_URL = "https://kamronking.github.io/obor-bot/"

active_orders_lock = {}


def get_sheet():
    try:
        raw_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        if not raw_json: return None
        creds_info = json.loads(raw_json.strip(), strict=False)
        creds = Credentials.from_service_account_info(creds_info, scopes=[
            "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(creds).open('Obor-bot-orders').get_worksheet(0)
    except:
        return None


sheet = get_sheet()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Сделать заказ / Buyurtma berish",
                        web_app=WebAppInfo(url=f"{WEB_APP_URL}?v={int(time.time())}"))]
    ], resize_keyboard=True)
    await message.answer("🇷🇺 Нажмите кнопку ниже для заказа.\n🇺🇿 Buyurtma berish uchun bosing.", reply_markup=kb)


@dp.message(F.web_app_data)
async def handle_webapp(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        oid = f"{datetime.now().strftime('%H%M')}-{random.randint(10, 99)}"
        lang = data.get('lang', 'ru')
        price = data.get('price', 7000)

        if data.get('type') == 'parcel':
            details = (f"📦 <b>ПОСЫЛКА:</b> {data.get('what')}\n"
                       f"👤 От: {data.get('name')} ({data.get('phone')})\n"
                       f"👤 Кому: {data.get('rec_name')} ({data.get('rec_phone')})")
        else:
            details = (f"🛒 <b>ПРОДУКТЫ:</b> {data.get('what')}\n"
                       f"👤 Имя: {data.get('name')} ({data.get('phone')})")

        url_a = f"https://www.google.com/maps?q={data.get('lat_from')},{data.get('lon_from')}"
        url_b = f"https://www.google.com/maps?q={data.get('lat_to')},{data.get('lon_to')}"

        text_adm = (f"🚚 <b>НОВЫЙ ЗАКАЗ #{oid}</b>\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"{details}\n"
                    f"💰 <b>Сумма:</b> {price:,} UZS\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"📍 <a href='{url_a}'>Точка А (Откуда)</a>\n"
                    f"🏁 <a href='{url_b}'>Точка Б (Куда)</a>")

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚕 ПРИНЯТЬ", callback_data=f"acc_{oid}_{message.from_user.id}_{lang}")]
        ])

        if sheet:
            sheet.append_row([oid, datetime.now().strftime('%d.%m %H:%M'), data.get('name'), data.get('phone'), details,
                              f"{price} UZS", "🆕"])

        for aid in ADMIN_IDS:
            await bot.send_message(aid, text_adm, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)

        await message.answer("✅ Отправлено!" if lang == 'ru' else "✅ Yuborildi!")
    except Exception as e:
        print(f"Error: {e}")


@dp.callback_query(F.data.startswith("acc_"))
async def accept(callback: CallbackQuery):
    _, oid, uid, lang = callback.data.split("_")
    if oid in active_orders_lock:
        return await callback.answer("❌ Занято!" if lang == 'ru' else "❌ Band!", show_alert=True)

    active_orders_lock[oid] = callback.from_user.first_name
    kb_done = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏁 ДОСТАВЛЕНО", callback_data=f"done_{oid}_{uid}_{lang}")]])
    await callback.message.edit_text(callback.message.html_text + f"\n\n🤝 <b>Взял: {callback.from_user.first_name}</b>",
                                     reply_markup=kb_done, parse_mode="HTML")
    await bot.send_message(uid,
                           f"🚕 Курьер {callback.from_user.first_name} принял заказ!" if lang == 'ru' else f"🚕 Kuryer {callback.from_user.first_name} qabul qildi!")


@dp.callback_query(F.data.startswith("done_"))
async def done(callback: CallbackQuery):
    _, oid, uid, lang = callback.data.split("_")
    await callback.message.edit_text(callback.message.html_text + "\n\n✅ <b>ДОСТАВЛЕНО</b>", reply_markup=None,
                                     parse_mode="HTML")
    await bot.send_message(uid, "🏁 Доставлено!" if lang == 'ru' else "🏁 Yetkazildi!")


async def main(): await dp.start_polling(bot)


if __name__ == '__main__': asyncio.run(main())