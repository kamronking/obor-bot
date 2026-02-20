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

# Загрузка настроек
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
WEB_APP_URL = "https://kamronking.github.io/obor-bot/"

# Защита от двойного принятия заказа
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
        creds_info = json.loads(raw_json.strip(), strict=False)
        creds = Credentials.from_service_account_info(creds_info,
                                                      scopes=["https://www.googleapis.com/auth/spreadsheets",
                                                              "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open('Obor-bot-orders').get_worksheet(0)
    except:
        return None


sheet = get_sheet()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: Message):
    cache_url = f"{WEB_APP_URL}?v={int(time.time())}"
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚀 Заказать / Buyurtma", web_app=WebAppInfo(url=cache_url))]],
        resize_keyboard=True)

    welcome = (
        "👋 <b>Obor Delivery</b>\n\n"
        "🇷🇺 Нажмите кнопку ниже для заказа\n"
        "🇺🇿 Buyurtma berish uchun tugmani bosing"
    )
    await message.answer(welcome, reply_markup=kb, parse_mode="HTML")


@dp.message(F.web_app_data)
async def handle_webapp(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        oid = f"{datetime.now().strftime('%H%M')}-{random.randint(10, 99)}"
        dist = haversine(data['lat_from'], data['lon_from'], data['lat_to'], data['lon_to'])
        lang = data.get('lang', 'ru')

        cat = "📦 Посылка" if data['type'] == 'parcel' else "🛒 Продукты"
        w_str = f" ({data.get('weight')} кг)" if data['type'] == 'parcel' else ""

        if sheet:
            try:
                sheet.append_row([oid, datetime.now().strftime('%d.%m %H:%M'), data['name'], data['phone'],
                                  f"{cat}{w_str}: {data['what']}", f"{data['price']} UZS", "🆕"])
            except:
                pass

        url_a = f"https://www.google.com/maps?q={data['lat_from']},{data['lon_from']}"
        url_b = f"https://www.google.com/maps?q={data['lat_to']},{data['lon_to']}"

        text_adm = (f"🚚 <b>ЗАКАЗ #{oid}</b>\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🗂 <b>Тип:</b> {cat}{w_str}\n"
                    f"📦 <b>Что:</b> {data['what']}\n"
                    f"💰 <b>Цена:</b> <b>{data['price']:,} UZS</b>\n"
                    f"📏 <b>Дистанция:</b> {dist:.1f} км\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"👤 <b>Клиент:</b> {data['name']}\n"
                    f"📞 <b>Тел:</b> {data['phone']}\n\n"
                    f"📍 <a href='{url_a}'>ТОЧКА А (Откуда)</a>\n"
                    f"🏁 <a href='{url_b}'>ТОЧКА Б (Куда)</a>")

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚕 ПРИНЯТЬ ЗАКАЗ", callback_data=f"acc_{oid}_{message.from_user.id}_{lang}")]])

        for aid in ADMIN_IDS:
            await bot.send_message(aid, text_adm, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)

        resp = "✅ <b>Заказ №" + oid + " оформлен!</b>\nОжидайте звонка." if lang == 'ru' else "✅ <b>Buyurtma №" + oid + " qabul qilindi!</b>\nTelefonni kuting."
        await message.answer(resp, parse_mode="HTML")

    except Exception as e:
        print(f"ERR: {e}")


@dp.callback_query(F.data.startswith("acc_"))
async def accept(callback: CallbackQuery):
    _, oid, uid, lang = callback.data.split("_")
    if oid in active_orders_lock: return await callback.answer("Уже принято!", show_alert=True)

    active_orders_lock[oid] = callback.from_user.first_name
    kb_done = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏁 ДОСТАВЛЕНО", callback_data=f"done_{oid}_{uid}_{lang}")]])

    await callback.message.edit_text(callback.message.html_text + f"\n\n🤝 <b>Взял: {callback.from_user.first_name}</b>",
                                     reply_markup=kb_done, parse_mode="HTML", disable_web_page_preview=True)

    msg = f"🚕 Курьер {callback.from_user.first_name} принял заказ №{oid}!" if lang == 'ru' else f"🚕 Kuryer {callback.from_user.first_name} buyurtmani qabul qildi №{oid}!"
    await bot.send_message(uid, msg)
    await callback.answer()


@dp.callback_query(F.data.startswith("done_"))
async def done(callback: CallbackQuery):
    _, oid, uid, lang = callback.data.split("_")
    if oid in active_orders_lock: del active_orders_lock[oid]

    await callback.message.edit_text(callback.message.html_text + "\n✅ <b>СТАТУС: ЗАВЕРШЕН</b>", reply_markup=None,
                                     parse_mode="HTML")

    msg = "🏁 Ваш заказ №" + oid + " доставлен!" if lang == 'ru' else "🏁 Buyurtmangiz №" + oid + " yetkazildi!"
    await bot.send_message(uid, msg)
    await callback.answer("Завершено!")


async def main(): await dp.start_polling(bot)


if __name__ == '__main__': asyncio.run(main())