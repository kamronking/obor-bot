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
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
WEB_APP_URL = "https://kamronking.github.io/obor-bot/"  # Твоя ссылка

# Глобальный словарь для блокировки заказов
# { "order_id": "имя_курьера" }
active_orders_lock = {}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Заказать / Buyurtma berish",
                        web_app=WebAppInfo(url=f"{WEB_APP_URL}"))]
    ], resize_keyboard=True)
    await message.answer("🇷🇺 Сделайте заказ через приложение.\n🇺🇿 Ilova orqali buyurtma bering.", reply_markup=kb)


@dp.message(F.web_app_data)
async def handle_webapp(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        oid = f"{datetime.now().strftime('%H%M')}-{random.randint(10, 99)}"
        lang = data.get('lang', 'ru')

        if data['type'] == 'parcel':
            details = (f"📦 <b>ПОСЫЛКА (POSILKA)</b>\n"
                       f"📝 Что: {data['what']}\n"
                       f"👤 От: {data['name']} ({data['phone']})\n"
                       f"👤 Кому: {data['rec_name']} ({data['rec_phone']})")
            loc_info = "📍 <i>Адрес уточнить у клиента (Zvonok)</i>"
        else:
            details = (f"🛒 <b>ПРОДУКТЫ (MAHSULOTLAR)</b>\n"
                       f"📝 Список: {data['what']}\n"
                       f"👤 Клиент: {data['name']} ({data['phone']})")
            url = f"https://www.google.com/maps?q={data['lat']},{data['lon']}"
            loc_info = f"📍 <a href='{url}'>ОТКРЫТЬ КАРТУ (LOKATSIYA)</a>"

        text_adm = (f"🚚 <b>НОВЫЙ ЗАКАЗ #{oid}</b>\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"{details}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"{loc_info}")

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚕 ПРИНЯТЬ (QABUL QILISH)",
                                  callback_data=f"acc_{oid}_{message.from_user.id}_{lang}")]
        ])

        for aid in ADMIN_IDS:
            await bot.send_message(aid, text_adm, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)

        resp = "✅ Отправлено! Курьер свяжется." if lang == 'ru' else "✅ Yuborildi! Kuryer bog'lanadi."
        await message.answer(resp)
    except Exception as e:
        print(f"Error handling WebApp: {e}")


@dp.callback_query(F.data.startswith("acc_"))
async def accept_order(callback: CallbackQuery):
    _, oid, uid, lang = callback.data.split("_")

    # ПРОВЕРКА БЛОКИРОВКИ: Если заказ уже в словаре — значит его кто-то взял
    if oid in active_orders_lock:
        already_taken_by = active_orders_lock[oid]
        msg = f"❌ Заказ #{oid} уже взял курьер {already_taken_by}!"
        return await callback.answer(msg, show_alert=True)

    # Регистрация курьера
    active_orders_lock[oid] = callback.from_user.first_name

    # Обновляем сообщение для всех админов (чтобы видели, кто взял)
    new_text = callback.message.html_text + f"\n\n🤝 <b>ВЗЯЛ: {callback.from_user.first_name}</b>"
    await callback.message.edit_text(new_text, reply_markup=None, parse_mode="HTML", disable_web_page_preview=True)

    # Уведомляем клиента
    msg_client = f"🚕 Курьер {callback.from_user.first_name} принял ваш заказ!" if lang == 'ru' else f"🚕 Kuryer {callback.from_user.first_name} buyurtmangizni qabul qildi!"
    try:
        await bot.send_message(uid, msg_client)
    except:
        pass

    await callback.answer("Заказ принят! / Qabul qilindi!")


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())