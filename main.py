import asyncio
import re
import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery,
    WebAppInfo
)

# Загружаем переменные
load_dotenv()

# ИМПОРТ ФУНКЦИЙ
from google_sheets import append_order, update_order_status, get_stats

# --- НАСТРОЙКИ ---
TOKEN = os.getenv('BOT_TOKEN')
try:
    COURIER_ID = int(os.getenv('COURIER_ID', 0))
    ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
except (TypeError, ValueError):
    COURIER_ID = 0
    ADMIN_ID = 0

# ССЫЛКА НА ВАШ MINI APP (GitHub Pages)
WEB_APP_URL = "https://kamronking.github.io/obor-bot/"

TIMEZONE = ZoneInfo("Asia/Tashkent")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher(storage=MemoryStorage())
router = Router()

LANGUAGE = {}


class OrderForm(StatesGroup):
    ChoosingLanguage = State()
    ChoosingType = State()
    WaitingForSource = State()
    WaitingForWhat = State()
    WaitingForWeight = State()
    WaitingForDropoff = State()
    WaitingForName = State()
    WaitingForPhone = State()
    ConfirmingOrder = State()


class AdminStates(StatesGroup):
    WaitingForBroadcast = State()


TEXTS = {
    'ru': {
        'open_app': '📝 Заполнить форму заказа',
        'ask_app': 'Пожалуйста, нажмите кнопку ниже, чтобы ввести имя и телефон:',
        'ask_type': '🚚 <b>Выберите тип доставки:</b>',
        'type_buy': '🛍 Покупка',
        'type_send': '📦 Посылка',
        'ask_weight': '⚖️ <b>Введите вес (например: 2 кг):</b>',
        'ask_where_from': '🛒 <b>Откуда забрать?</b>',
        'ask_what': '📦 <b>Что именно нужно привезти?</b>',
        'ask_dropoff': '📍 <b>Отправьте вашу локацию кнопкой:</b>',
        'summary_title': '📋 <b>Ваш заказ:</b>\n',
        'summary_item': '🔹 {ot}: {ss} -> {sw} ({w})\n',
        'summary_footer': '\n🙋‍♂️ Имя: {sn}\n📱 Тел: {ph}',
        'btn_send': '✅ Оформить заказ',
        'btn_add': '➕ Добавить еще товар',
        'confirm': '✅ <b>Заказ №{id} принят!</b>',
        'err_text': '⚠️ Минимум 2 символа!',
        'err_type': '⚠️ Выберите вариант из меню.',
        'err_loc': '⚠️ Нажмите на кнопку 📍 Локация.',
        'btn_cancel': '❌ Отмена заказа',
        'order_accepted': '🚕 Ваш заказ <b>#{id}</b> принят!',
        'order_delivered': '🏁 Ваш заказ <b>#{id}</b> доставлен!',
        'cancel_success': '🚫 Отменено.'
    },
    'uz': {
        'open_app': '📝 Buyurtma formasini toʻldirish',
        'ask_app': 'Ism va telefon raqamingizni kiritish uchun tugmani bosing:',
        'ask_type': '🚚 <b>Yetkazib berish turini tanlang:</b>',
        'type_buy': '🛍 Xarid qilish',
        'type_send': '📦 Posilka',
        'ask_weight': '⚖️ <b>Vaznni kiriting:</b>',
        'ask_where_from': '🛒 <b>Qayerdan olib kelish kerak?</b>',
        'ask_what': '📦 <b>Nima olib kelish kerak?</b>',
        'ask_dropoff': '📍 <b>Lokatsiyangizni yuboring:</b>',
        'summary_title': '📋 <b>Sizning buyurtmangiz:</b>\n',
        'summary_item': '🔹 {ot}: {ss} -> {sw} ({w})\n',
        'summary_footer': '\n🙋‍♂️ Ism: {sn}\n📱 Tel: {ph}',
        'btn_send': '✅ Tasdiqlash',
        'btn_add': '➕ Yana qoʻshish',
        'confirm': '✅ <b>Buyurtma №{id} qabul qilindi!</b>',
        'err_text': '⚠️ Kamida 2 ta belgi!',
        'err_type': '⚠️ Menyudan tanlang.',
        'err_loc': '⚠️ 📍 tugmasini bosing.',
        'btn_cancel': '❌ Bekor qilish',
        'order_accepted': '🚕 <b>#{id}</b> qabul qilindi!',
        'order_delivered': '🏁 <b>#{id}</b> yetkazildi!',
        'cancel_success': '🚫 Bekor qilindi.'
    }
}


# --- АДМИН ПАНЕЛЬ (без изменений) ---
@router.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='📊 Статистика'), KeyboardButton(text='📢 Рассылка')],
        [KeyboardButton(text='🏠 Выйти')]
    ], resize_keyboard=True)
    await message.answer("🛠 <b>Панель администратора</b>", reply_markup=kb)


@router.message(F.text == "📊 Статистика", F.from_user.id == ADMIN_ID)
async def show_stats_handler(message: Message):
    stats = get_stats()
    now = datetime.now(TIMEZONE).strftime("%H:%M:%S | %d.%m.%Y")
    msg = (f"📊 <b>СТАТИСТИКА ЗАКАЗОВ</b>\n━━━━━━━━━━━━━━━━━━\n"
           f"📦 Всего: <b>{stats['total']}</b>\n✅ Готово: <b>{stats['done']}</b>\n"
           f"🚕 В пути: <b>{stats['in_progress']}</b>\n\n🕒 <i>{now}</i>")
    await message.answer(msg)


# --- ПРОЦЕСС ЗАКАЗА ЧЕРЕЗ MINI APP ---

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    kb = [[KeyboardButton(text='🚀 Заказать/Buyurtma berish')]]
    if message.from_user.id == ADMIN_ID: kb.append([KeyboardButton(text='/admin')])
    await message.answer("👋 Привет! Я бот доставки Obor.",
                         reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))


@router.message(F.text.contains('Заказать'))
async def start_order(message: Message, state: FSMContext):
    await state.update_data(items=[])
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='🇷🇺 Русский'), KeyboardButton(text='🇺🇿 Oʻzbekcha')]],
                             resize_keyboard=True)
    await message.answer("🌐 Выберите язык / Tilni tanlang:", reply_markup=kb)
    await state.set_state(OrderForm.ChoosingLanguage)


@router.message(OrderForm.ChoosingLanguage, F.text)
async def language_selected(message: Message, state: FSMContext):
    lang = 'ru' if 'Русский' in message.text else 'uz'
    LANGUAGE[message.from_user.id] = lang

    # Кнопка для открытия Mini App
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=TEXTS[lang]['open_app'], web_app=WebAppInfo(url=WEB_APP_URL))],
        [KeyboardButton(text=TEXTS[lang]['btn_cancel'])]
    ], resize_keyboard=True)

    await message.answer(TEXTS[lang]['ask_app'], reply_markup=kb)


@router.message(F.web_app_data)
async def handle_webapp_data(message: Message, state: FSMContext):
    lang = LANGUAGE.get(message.from_user.id, 'ru')
    try:
        data = json.loads(message.web_app_data.data)
        name = data.get('name')
        phone = data.get('phone')

        await state.update_data(name=name, phone=phone)
        await message.answer(f"✅ {name}, данные приняты!")
        await ask_type(message, state, lang)
    except Exception as e:
        await message.answer("❌ Ошибка получения данных из формы.")


async def ask_type(message: Message, state: FSMContext, lang: str):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=TEXTS[lang]['type_buy']), KeyboardButton(text=TEXTS[lang]['type_send'])],
                  [KeyboardButton(text=TEXTS[lang]['btn_cancel'])]], resize_keyboard=True)
    await message.answer(TEXTS[lang]['ask_type'], reply_markup=kb)
    await state.set_state(OrderForm.ChoosingType)


@router.message(OrderForm.ChoosingType, F.text)
async def type_selected(message: Message, state: FSMContext):
    lang = LANGUAGE.get(message.from_user.id, 'ru')
    if message.text not in [TEXTS[lang]['type_buy'], TEXTS[lang]['type_send']]:
        return await message.answer(TEXTS[lang]['err_type'])
    await state.update_data(current_type=message.text)
    await message.answer(TEXTS[lang]['ask_where_from'], reply_markup=get_cancel_kb(lang))
    await state.set_state(OrderForm.WaitingForSource)


@router.message(OrderForm.WaitingForSource, F.text)
async def source_received(message: Message, state: FSMContext):
    lang = LANGUAGE.get(message.from_user.id, 'ru')
    if len(str(message.text)) < 2: return await message.answer(TEXTS[lang]['err_text'])
    await state.update_data(current_source=message.text)
    await message.answer(TEXTS[lang]['ask_what'], reply_markup=get_cancel_kb(lang))
    await state.set_state(OrderForm.WaitingForWhat)


@router.message(OrderForm.WaitingForWhat, F.text)
async def what_received(message: Message, state: FSMContext):
    lang = LANGUAGE.get(message.from_user.id, 'ru')
    if len(str(message.text)) < 2: return await message.answer(TEXTS[lang]['err_text'])
    await state.update_data(current_what=message.text)
    await message.answer(TEXTS[lang]['ask_weight'], reply_markup=get_cancel_kb(lang))
    await state.set_state(OrderForm.WaitingForWeight)


@router.message(OrderForm.WaitingForWeight, F.text)
async def weight_received(message: Message, state: FSMContext):
    lang = LANGUAGE.get(message.from_user.id, 'ru')
    data = await state.get_data()
    items = data.get('items', [])
    items.append(
        {'ot': data['current_type'], 'ss': data['current_source'], 'sw': data['current_what'], 'w': message.text})
    await state.update_data(items=items)

    if 'dropoff' not in data:
        kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='📍 Локация', request_location=True)],
                                           [KeyboardButton(text=TEXTS[lang]['btn_cancel'])]], resize_keyboard=True)
        await message.answer(TEXTS[lang]['ask_dropoff'], reply_markup=kb)
        await state.set_state(OrderForm.WaitingForDropoff)
    else:
        await show_summary(message, state, lang)


@router.message(OrderForm.WaitingForDropoff)
async def handle_dropoff(message: Message, state: FSMContext):
    lang = LANGUAGE.get(message.from_user.id, 'ru')
    if not message.location: return await message.answer(TEXTS[lang]['err_loc'])
    await state.update_data(dropoff=[message.location.latitude, message.location.longitude])
    await show_summary(message, state, lang)


async def show_summary(message: Message, state: FSMContext, lang: str):
    data = await state.get_data()
    summary = TEXTS[lang]['summary_title']
    for i in data['items']: summary += TEXTS[lang]['summary_item'].format(ot=i['ot'], ss=i['ss'], sw=i['sw'], w=i['w'])
    summary += TEXTS[lang]['summary_footer'].format(sn=data['name'], ph=data['phone'])
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=TEXTS[lang]['btn_send'])], [KeyboardButton(text=TEXTS[lang]['btn_add'])],
                  [KeyboardButton(text=TEXTS[lang]['btn_cancel'])]], resize_keyboard=True)
    await message.answer(summary, reply_markup=kb)
    await state.set_state(OrderForm.ConfirmingOrder)


@router.message(OrderForm.ConfirmingOrder)
async def process_confirm(message: Message, state: FSMContext):
    lang = LANGUAGE.get(message.from_user.id, 'ru')
    if message.text == TEXTS[lang]['btn_add']:
        await ask_type(message, state, lang)
    elif message.text == TEXTS[lang]['btn_send']:
        data = await state.get_data()
        order_id = str(int(datetime.now().timestamp()) % 1000)
        items_str = "".join([f"[{i['ot']}] {i['ss']}->{i['sw']} ({i['w']}); " for i in data['items']])

        append_order(
            {"order_id": order_id, "time": datetime.now(TIMEZONE).strftime("%d.%m %H:%M"), "first_name": data['name'],
             "phone": data['phone'], "items": items_str, "status": "🆕 НОВЫЙ"})

        await message.answer(TEXTS[lang]['confirm'].format(id=order_id), reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text='🚀 Заказать/Buyurtma berish')]], resize_keyboard=True))

        coords = data.get('dropoff', [0, 0])
        msg = f"🚚 <b>ЗАКАЗ #{order_id}</b>\n\n{items_str}\n\n👤 {data['name']}\n📞 {data['phone']}\n📍 <a href='http://maps.google.com/maps?q={coords[0]},{coords[1]}'>ЛОКАЦИЯ</a>"

        await bot.send_message(COURIER_ID, msg, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Взять", callback_data=f"accept_{order_id}_{message.from_user.id}")]]),
                               disable_web_page_preview=True)
        await state.clear()


# --- КУРЬЕРСКИЕ КОЛБЭКИ (без изменений) ---
@router.callback_query(F.data.startswith("accept_"))
async def courier_accept(callback: CallbackQuery):
    _, order_id, user_id = callback.data.split("_")
    update_order_status(order_id, "🚕 В ПУТИ")
    new_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏁 Доставлено!", callback_data=f"done_{order_id}_{user_id}")]])
    await callback.message.edit_reply_markup(reply_markup=new_kb)
    lang = LANGUAGE.get(int(user_id), 'ru')
    try:
        await bot.send_message(user_id, TEXTS[lang]['order_accepted'].format(id=order_id))
    except:
        pass


@router.callback_query(F.data.startswith("done_"))
async def courier_done(callback: CallbackQuery):
    _, order_id, user_id = callback.data.split("_")
    update_order_status(order_id, "🏁 ЗАВЕРШЕН")
    await callback.message.edit_text(callback.message.html_text + "\n\n✅ <b>ИСПОЛНЕНО</b>", reply_markup=None)
    lang = LANGUAGE.get(int(user_id), 'ru')
    try:
        await bot.send_message(user_id, TEXTS[lang]['order_delivered'].format(id=order_id))
    except:
        pass


def get_cancel_kb(lang):
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=TEXTS[lang]['btn_cancel'])]], resize_keyboard=True)


@router.message(F.text.in_(['❌ Отмена заказа', '❌ Bekor qilish', '🏠 Выйти']))
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    lang = LANGUAGE.get(message.from_user.id, 'ru')
    await message.answer(TEXTS[lang]['cancel_success'], reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='🚀 Заказать/Buyurtma berish')]], resize_keyboard=True))


async def main():
    dp.include_router(router)
    print("✅ Бот запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())