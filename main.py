import asyncio
import os
import json
import random
import re
import gspread
import time
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
        print(f"❌ Google Sheets Error: {e}")
        return None


sheet = get_sheet()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: Message):
    cache_url = f"{WEB_APP_URL}?v={int(time.time())}"
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Заказать / Buyurtma berish", web_app=WebAppInfo(url=cache_url))]
    ], resize_keyboard=True)

    # Двуязычное приветствие
    welcome_text = (
        "👋 <b>Obor Delivery</b>\n\n"
        "🇷🇺 Нажмите кнопку ниже, чтобы запустить приложение и сделать заказ.\n"
        "🇺🇿 Buyurtma berish uchun pastdagi tugmani bosing."
    )
    await message.answer(welcome_text, reply_markup=kb, parse_mode="HTML")


@dp.message(F.web_app_data)
async def handle_webapp(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        oid = f"{datetime.now().strftime('%H%M')}-{random.randint(10, 99)}"
        dist = haversine(data['lat_from'], data['lon_from'], data['lat_to'], data['lon_to'])

        is_parcel = data['type'] == 'parcel'
        cat = "📦 Посылка" if is_parcel else "🛒 Продукты"
        weight_str = f" ({data.get('weight', 1)} кг)" if is_parcel else ""

        if sheet:
            try:
                sheet.append_row(
                    [oid, datetime.now().strftime('%d.%m %H:%M'), data['name'], data['phone'], f"{cat}{weight_str}",
                     f"{data['price']} UZS", "🆕 НОВЫЙ"])
            except:
                pass

        url_a = f"https://www.google.com/maps?q={data['lat_from']},{data['lon_from']}"
        url_b = f"https://www.google.com/maps?q={data['lat_to']},{data['lon_to']}"

        # Исправлено: убраны лишние пробелы в тегах, чтобы не было ошибок <b/>
        text = (f"🚚 <b>НОВЫЙ ЗАКАЗ #{oid}</b>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🗂 <b>Тип:</b> {cat}{weight_str}\n"
                f"📦 <b>Что:</b> {data['what']}\n"
                f"💰 <b>Цена:</b> <b>{data['price']:,} UZS</b>\n"
                f"📏 <b>Путь:</b> {dist:.1f} км\n"
                f"━━━━━━━━━━━━━━━\n"
                f"👤 <b>Имя:</b> {data['name']}\n"
                f"📞 <b>Тел:</b> {data['phone']}\n\n"
                f"📍 <a href='{url_a}'>ТОЧКА А</a>\n"
                f"🏁 <a href='{url_b}'>ТОЧКА Б</a>")

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚕 ПРИНЯТЬ", callback_data=f"acc_{oid}_{message.from_user.id}")]])

        for aid in ADMIN_IDS:
            await bot.send_message(aid, text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)

        # Ответ пользователю без лишних символов
        await message.answer(
            f"✅ <b>Заказ №{oid} оформлен!</b>\nСумма: <b>{data['price']:,} UZS</b>\n\nОжидайте звонка курьера.",
            parse_mode="HTML")

    except Exception as e:
        print(f"Error: {e}")


@dp.callback_query(F.data.startswith("acc_"))
async def accept(callback: CallbackQuery):
    _, oid, uid = callback.data.split("_")
    if oid in active_orders_lock:
        return await callback.answer("Уже занято!", show_alert=True)

    active_orders_lock[oid] = callback.from_user.first_name
    await callback.message.edit_text(callback.message.html_text + f"\n\n🤝 <b>Взял: {callback.from_user.first_name}</b>",
                                     parse_mode="HTML", disable_web_page_preview=True)
    await bot.send_message(uid, f"🚕 Курьер принял ваш заказ №{oid}!")
    await callback.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())