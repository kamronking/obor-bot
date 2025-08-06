from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.default import DefaultBotProperties
import asyncio
import json
import os
from datetime import datetime

TOKEN = '8451105651:AAHw21f-xCOAeh6V8nXu8n9DHDRt5wkCJBE'
COURIER_ID = 5345096255

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher(storage=MemoryStorage())
router = Router()

LANGUAGE = {}

TEXTS = {
    'ru': {
        'welcome': '👋 Привет! Я — бот доставки <b>Obor</b>!\n\nВыбери язык обслуживания:',
        'ask_where_from': '🛒 Откуда привезти товар? Напишите заведение или адрес.',
        'ask_what': '📦 Что нужно привезти?',
        'ask_dropoff': '📍 Пожалуйста, отправьте локацию, куда доставить.',
        'ask_name': '🙋‍♂️ Как вас зовут?',
        'ask_phone': '📱 Пожалуйста, отправьте номер телефона кнопкой ниже:',
        'confirm': '✅ Спасибо! Ваш заказ принят!\nНомер заказа: <b>#{id}</b>\nВремя: <b>{time}</b>\nСкоро свяжемся!',
        'main_menu': '🏠 Главное меню',
        'restart': '🔁 Начать заново',
        'order_cancelled': '❌ Заказ отменён.',
        'no_orders': '📊 Заказов пока нет.',
        'stats': '📈 Всего заказов: {count}\nОбщая сумма: {total} сум. ',
        'help_text': '🇷🇺 📞 Телефон для связи: +998 90 402 17 11. 🇺🇿 📞 Aloqa raqami: +998 90 402 17 11.',
        'tariff_text': '💸 Стоимость доставки:\n 🇷🇺 ▫️ Базовая цена — 7000 сум\n▫️ Плюс 1000 сум за каждый км.🇺🇿 💸 Yetkazib berish narxi:\n▫️ Asosiy narx — 7000 so‘m\n▫️ Har bir km uchun qo‘shimcha — 1000 so‘m',
        'about_us': '📖 <b>Кто мы?</b>\n\n🇷🇺 Мы — команда Obor. Наша цель — сделать доставку в Гулистане быстрой, удобной и доступной. Мы доставляем всё: еду, товары, документы и многое другое. 🇺🇿 Biz — Obor jamoasimiz. Maqsadimiz — Gulistonda yetkazib berishni tez, qulay va arzon qilish. Biz hamma narsani yetkazamiz: ovqat, mahsulotlar, hujjatlar va boshqalar.',
    },
    'uz': {
        'welcome': '👋 Salom! Men — <b>Obor</b> yetkazib berish boti!\n\nIltimos, xizmat tilini tanlang:',
        'ask_where_from': '🛒 Mahsulotni qayerdan olib kelish kerak? Joy nomini yozing.',
        'ask_what': '📦 Nima olib kelish kerak?',
        'ask_dropoff': '📍 Iltimos, qayerga yetkazish kerakligini lokatsiya orqali yuboring.',
        'ask_name': '🙋‍♂️ Ismingiz nima?',
        'ask_phone': '📱 Telefon raqamingizni quyidagi tugma orqali yuboring:',
        'confirm': '✅ Rahmat! Buyurtmangiz qabul qilindi!\nBuyurtma raqami: <b>#{id}</b>\nVaqti: <b>{time}</b>\nTez orada bog‘lanamiz!',
        'main_menu': '🏠 Asosiy menyu',
        'restart': '🔁 Qayta boshlash',
        'order_cancelled': '❌ Buyurtma bekor qilindi.',
        'no_orders': '📊 Hozircha buyurtmalar yo‘q.',
        'stats': '📈 Jami buyurtmalar: {count}\nUmumiy summa: {total} so‘m',
        'help_text': ' 🇺🇿 📞 Aloqa raqami: +998 90 402 17 11. 🇷🇺  📞 Телефон для связи: +998 90 402 17 11',
        'tariff_text': '💸 Yetkazib berish narxi:\n 🇺🇿 ▫️ Asosiy narx — 7000 so‘m\n▫️ Har bir km uchun qo‘shimcha — 1000 so‘m. 💸 Стоимость доставки:\n 🇷🇺 ▫️ Базовая цена — 7000 сум\n▫️ Плюс 1000 сум за каждый км.',
        'about_us': '📖 <b>Biz kim?</b>\n\n🇺🇿 Biz — Obor jamoasimiz. Maqsadimiz — Gulistonda yetkazib berishni tez, qulay va arzon qilish. Biz hamma narsani yetkazamiz: ovqat, mahsulotlar, hujjatlar va boshqalar. 🇷🇺 Мы — команда Obor. Наша цель — сделать доставку в Гулистане быстрой, удобной и доступной. Мы доставляем всё: еду, товары, документы и многое другое.',
    }
}

class OrderForm(StatesGroup):
    ChoosingLanguage = State()
    WaitingForSource = State()
    WaitingForWhat = State()
    WaitingForDropoff = State()
    WaitingForName = State()
    WaitingForPhone = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='🚀 Заказать/Buyurtma berish')],
            [KeyboardButton(text='📞 Помощь / Yordam'), KeyboardButton(text='💸 Тарифы / Narxlar')],
            [KeyboardButton(text='ℹ️ Кто мы / Biz kim')]
        ],
        resize_keyboard=True
    )
    await message.answer("👋 Привет! Salom!\n\nВыберите действие: Amalni tanlang:", reply_markup=kb)
    await state.clear()

# 🛠 Исправлено: поддержка всех возможных вариантов текста кнопки "Заказать"
@router.message(F.text.in_(['🚀 Заказать/Buyurtma berish', 'Заказать', 'Buyurtma berish']))
async def start_order(message: Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='🇷🇺 Русский'), KeyboardButton(text='🇺🇿 Oʻzbekcha')]],
        resize_keyboard=True
    )
    await message.answer("🌐 Выберите язык / Tilni tanlang:", reply_markup=kb)
    await state.set_state(OrderForm.ChoosingLanguage)

@router.message(F.text.in_(['🇷🇺 Русский', '🇺🇿 Oʻzbekcha']))
async def language_selected(message: Message, state: FSMContext):
    lang = 'ru' if 'Русский' in message.text else 'uz'
    LANGUAGE[message.from_user.id] = lang
    clean_kb = ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)
    await message.answer(TEXTS[lang]['ask_where_from'], reply_markup=clean_kb)
    await state.set_state(OrderForm.WaitingForSource)

@router.message(OrderForm.WaitingForSource)
async def source_received(message: Message, state: FSMContext):
    await state.update_data(source=message.text)
    lang = LANGUAGE.get(message.from_user.id, 'ru')
    await message.answer(TEXTS[lang]['ask_what'])
    await state.set_state(OrderForm.WaitingForWhat)

@router.message(OrderForm.WaitingForWhat)
async def what_received(message: Message, state: FSMContext):
    await state.update_data(what=message.text)
    lang = LANGUAGE.get(message.from_user.id, 'ru')
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='📍 Отправить локацию', request_location=True)]],
        resize_keyboard=True
    )
    await message.answer(TEXTS[lang]['ask_dropoff'], reply_markup=kb)
    await state.set_state(OrderForm.WaitingForDropoff)

@router.message(OrderForm.WaitingForDropoff)
async def handle_dropoff(message: Message, state: FSMContext):
    lang = LANGUAGE.get(message.from_user.id, 'ru')
    if not message.location:
        await message.answer(TEXTS[lang]['ask_dropoff'])
        return
    dropoff = (message.location.latitude, message.location.longitude)
    await state.update_data(dropoff=dropoff)
    await message.answer(TEXTS[lang]['ask_name'])
    await state.set_state(OrderForm.WaitingForName)

@router.message(OrderForm.WaitingForName)
async def name_received(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    lang = LANGUAGE.get(message.from_user.id, 'ru')
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='📲 Отправить номер телефона', request_contact=True)]],
        resize_keyboard=True
    )
    await message.answer(TEXTS[lang]['ask_phone'], reply_markup=kb)
    await state.set_state(OrderForm.WaitingForPhone)

@router.message(OrderForm.WaitingForPhone, F.contact)
async def contact_received(message: Message, state: FSMContext):
    data = await state.get_data()
    phone = message.contact.phone_number
    order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    order_id = save_order({
        "user_id": message.from_user.id,
        "source": data['source'],
        "what": data['what'],
        "dropoff": data['dropoff'],
        "name": data['name'],
        "phone": phone,
        "time": order_time
    })
    lang = LANGUAGE.get(message.from_user.id, 'ru')
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='🚀 Заказать/Buyurtma berish')],
            [KeyboardButton(text='📞 Помощь / Yordam'), KeyboardButton(text='💸 Тарифы / Narxlar')],
            [KeyboardButton(text='ℹ️ Кто мы / Biz kim')]
        ],
        resize_keyboard=True
    )
    await message.answer(TEXTS[lang]['confirm'].format(id=order_id, time=order_time), reply_markup=kb)
    await state.clear()

    lat, lon = data['dropoff']
    courier_text = (
        f"🚚 <b>Новый заказ!</b>\n\n"
        f"🛒 <b>Откуда:</b> {data['source']}\n"
        f"📦 <b>Что принести:</b> {data['what']}\n"
        f"📍 <b>Куда:</b> <a href='https://maps.google.com/?q={lat},{lon}'>Локация</a>\n"
        f"🙋‍♂️ <b>Имя:</b> {data['name']}\n"
        f"📱 <b>Телефон:</b> {phone}\n"
        f"🕒 <b>Время:</b> {order_time}\n"
        f"🔢 <b>Номер заказа:</b> #{order_id}"
    )
    try:
        await bot.send_message(chat_id=COURIER_ID, text=courier_text)
    except Exception as e:
        print(f"Ошибка отправки курьеру: {e}")

@router.message(F.text.in_(['📞 Помощь / Yordam']))
async def help_message(message: Message):
    lang = LANGUAGE.get(message.from_user.id, 'ru')
    await message.answer(TEXTS[lang]['help_text'])

@router.message(F.text.in_(['💸 Тарифы / Narxlar']))
async def show_tariffs(message: Message):
    lang = LANGUAGE.get(message.from_user.id, 'ru')
    await message.answer(TEXTS[lang]['tariff_text'])

@router.message(F.text.in_(['ℹ️ Кто мы / Biz kim']))
async def about_us(message: Message):
    lang = LANGUAGE.get(message.from_user.id, 'ru')
    await message.answer(TEXTS[lang]['about_us'])

def save_order(order_data):
    ORDER_FILE = "orders.json"
    if not os.path.exists(ORDER_FILE):
        with open(ORDER_FILE, 'w') as f:
            json.dump([], f)
    with open(ORDER_FILE, 'r') as f:
        orders = json.load(f)
    order_id = len(orders) + 1
    order_data['id'] = order_id
    orders.append(order_data)
    with open(ORDER_FILE, 'w') as f:
        json.dump(orders, f, indent=4, ensure_ascii=False)
    return order_id

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
