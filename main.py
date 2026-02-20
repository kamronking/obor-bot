import asyncio
import os
import json
import random
import re
import gspread
import time  # Добавлено для анти-кеша
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from math import radians, cos, sin, asin, sqrt

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
WEB_APP_URL = "https://kamronking.github.io/obor-bot/"

active_orders_lock = {}


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dLat, dLon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dLat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon / 2) ** 2
    return R * 2 * asin(sqrt(a))


def get_sheet():
    try:
        raw_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        if not raw_json: return None
        raw_json = raw_json.strip()
        raw_json = re.sub(r'[\x00-\x1F\x7F]', '', raw_json)
        creds_info = json.loads(raw_json, strict=False)
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(
            creds_info,
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open('Obor-bot-orders').get_worksheet(0)
    except Exception as e:
        print(f"❌ Ошибка Google Sheets: {e}")
        return None


sheet = get_sheet()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: Message):
    # Добавляем ?v=TIMESTAMP, чтобы Telegram не кешировал старый HTML
    cache_cleaner = int(time.time())
    url_with_no_cache = f"{WEB_APP_URL}?v={cache_cleaner}"

    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Заказать / Buyurtma", web_app=WebAppInfo(url=url_with_no_cache))]
    ], resize_keyboard=True)
    await message.answer("👋 <b>Obor Delivery</b>\nНажмите кнопку для заказа:", reply_markup=kb, parse_mode="HTML")


@dp.message(F.web_app_data)
async def handle_webapp(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        oid = f"{datetime.now().strftime('%H%M')}-{random.randint(10, 99)}"
        dist = haversine(data['lat_from'], data['lon_from'], data['lat_to'], data['lon_to'])
        cat = "📦 Посылка" if data['type'] == 'parcel' else "🛒 Продукты"

        if sheet:
            try:
                sheet.append_row(
                    [oid, datetime.now().strftime('%d.%m %H:%M'), data['name'], data['phone'], f"{cat}: {data['what']}",
                     f"{data['price']} UZS", "🆕 НОВЫЙ"])
            except:
                pass

        url_a = f"https://www.google.com/maps?q={data['lat_from']},{data['lon_from']}"
        url_b = f"https://www.google.com/maps?q={data['lat_to']},{data['lon_to']}"

        text = (f"🚚 <b>ЗАКАЗ #{oid}</b>\n━━━━━━━━━━━━━━━\n"
                f"Тип: {cat}\nЧто: {data['what']}\n"
                f"💰 Цена: <b>{data['price']:,} UZS</b>\n"
                f"📏 Дистанция: {dist:.1f} км\n━━━━━━━━━━━━━━━\n"
                f"👤 {data['name']} | {data['phone']}\n\n"
                f"📍 <a href='{url_a}'>ТОЧКА А</a> | 🏁 <a href='{url_b}'>ТОЧКА Б</a>")

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚕 ПРИНЯТЬ", callback_data=f"acc_{oid}_{message.from_user.id}")]])
        for aid in ADMIN_IDS:
            await bot.send_message(aid, text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)
        await message.answer(f"✅ Заказ №{oid} принят! Ожидайте звонка.")
    except Exception as e:
        print(f"Error handling webapp: {e}")


@dp.callback_query(F.data.startswith("acc_"))
async def accept(callback: CallbackQuery):
    _, oid, uid = callback.data.split("_")
    if oid in active_orders_lock: return await callback.answer("Уже занято!")
    active_orders_lock[oid] = callback.from_user.first_name
    await callback.message.edit_text(callback.message.html_text + f"\n\n🤝 <b>Взял: {callback.from_user.first_name}</b>",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                         [InlineKeyboardButton(text="🏁 ДОСТАВЛЕНО",
                                                               callback_data=f"done_{oid}_{uid}")]]), parse_mode="HTML")
    await bot.send_message(uid, f"🚕 Курьер {callback.from_user.first_name} принял ваш заказ №{oid}!")


@dp.callback_query(F.data.startswith("done_"))
async def done(callback: CallbackQuery):
    _, oid, uid = callback.data.split("_")
    if oid in active_orders_lock: del active_orders_lock[oid]
    await callback.message.edit_text(callback.message.html_text + "\n\n🏁 <b>СТАТУС: ДОСТАВЛЕНО</b>", reply_markup=None,
                                     parse_mode="HTML")
    await bot.send_message(uid, f"🏁 Заказ №{oid} доставлен! Спасибо.")


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())