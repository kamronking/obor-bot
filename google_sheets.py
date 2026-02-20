import os
import json
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials

# Настройки доступов
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def get_creds():
    creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if creds_json:
        try:
            creds_json = creds_json.replace('\\n', '\n').strip().strip("'").strip('"')
            return Credentials.from_service_account_info(json.loads(creds_json), scopes=SCOPES)
        except Exception as e:
            print(f"❌ Ошибка парсинга JSON: {e}")

    base_path = os.path.dirname(os.path.abspath(__file__))
    for file_name in ['credentials.json', 'credentials .json']:
        file_path = os.path.join(base_path, file_name)
        if os.path.exists(file_path):
            return Credentials.from_service_account_file(file_path, scopes=SCOPES)
    return None


# Глобальные переменные для двух листов
order_sheet = None
user_sheet = None

# Авторизация
try:
    creds = get_creds()
    if creds:
        client = gspread.authorize(creds)
        spreadsheet = client.open('Obor-bot-orders')

        # 1. Лист заказов (первая вкладка)
        order_sheet = spreadsheet.get_worksheet(0)

        # 2. Лист пользователей (ищем по названию "Users")
        try:
            user_sheet = spreadsheet.worksheet("Users")
            print(f"✅ Подключено. Заказы: {order_sheet.title}, Юзеры: {user_sheet.title}")
        except:
            print("⚠️ Лист 'Users' не найден! Создай вкладку с таким именем.")
            user_sheet = None
    else:
        print("⚠️ Ключи Google не найдены.")
except Exception as e:
    print(f"🚨 ОШИБКА GOOGLE: {e}")


# --- ФУНКЦИЯ ДЛЯ USERS ---
def track_user(user_id, name):
    if not user_sheet: return
    try:
        # Проверяем, есть ли уже такой ID в первой колонке
        ids = user_sheet.col_values(1)
        if str(user_id) not in ids:
            user_sheet.append_row([
                str(user_id),
                name,
                datetime.now().strftime('%d.%m.%Y %H:%M')
            ])
            print(f"👤 Новый пользователь {name} сохранен")
    except Exception as e:
        print(f"❌ Ошибка записи пользователя: {e}")


# --- ФУНКЦИИ ДЛЯ ЗАКАЗОВ ---
def append_order(order_data: dict):
    if not order_sheet: return
    try:
        row = [
            order_data.get('order_id', ''),
            order_data.get('time', ''),
            order_data.get('first_name', ''),
            order_data.get('phone', ''),
            order_data.get('items', ''),
            order_data.get('status', '🆕 НОВЫЙ')
        ]
        order_sheet.append_row(row)
    except Exception as e:
        print(f"❌ Ошибка записи заказа: {e}")


def update_order_status(order_id: str, new_status: str):
    if not order_sheet: return False
    try:
        cell = order_sheet.find(str(order_id))
        order_sheet.update_cell(cell.row, 6, new_status)
        return True
    except:
        return False
