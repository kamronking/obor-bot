import os
import json
import gspread
from google.oauth2.service_account import Credentials

# Настройки доступов
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def get_creds():
    # 1. Сначала ищем в переменных окружения (для Render)
    creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if creds_json:
        try:
            # Чистим от случайных кавычек по краям
            creds_json = creds_json.strip().strip("'").strip('"')
            return Credentials.from_service_account_info(json.loads(creds_json), scopes=SCOPES)
        except Exception as e:
            print(f"❌ Ошибка парсинга GOOGLE_CREDENTIALS_JSON: {e}")

    # 2. Если переменной нет, ищем файл (для MacBook)
    base_path = os.path.dirname(os.path.abspath(__file__))
    for file_name in ['credentials.json', 'credentials .json']:
        file_path = os.path.join(base_path, file_name)
        if os.path.exists(file_path):
            print(f"📂 Использую файл ключей: {file_name}")
            return Credentials.from_service_account_file(file_path, scopes=SCOPES)

    return None


# Авторизация
try:
    creds = get_creds()
    if creds:
        client = gspread.authorize(creds)
        # Убедись, что имя таблицы в Google совпадает!
        sheet = client.open('Obor-bot-orders').sheet1
        print("✅ Подключение к Google Таблицам установлено")
    else:
        print("⚠️ Внимание: Ключи Google не найдены.")
        sheet = None
except Exception as e:
    print(f"🚨 КРИТИЧЕСКАЯ ОШИБКА GOOGLE: {e}")
    sheet = None


def append_order(order_data: dict):
    if not sheet: return
    try:
        row = [
            order_data.get('order_id', ''),
            order_data.get('time', ''),
            order_data.get('first_name', ''),
            order_data.get('phone', ''),
            order_data.get('items', ''),
            order_data.get('status', '🆕 НОВЫЙ')
        ]
        sheet.append_row(row)
    except Exception as e:
        print(f"❌ Ошибка записи: {e}")


def update_order_status(order_id: str, new_status: str):
    if not sheet: return False
    try:
        cell = sheet.find(str(order_id))
        sheet.update_cell(cell.row, 6, new_status)
        return True
    except:
        return False


def get_stats():
    if not sheet: return {"total": 0, "done": 0, "in_progress": 0}
    try:
        data = sheet.get_all_values()
        if not data or len(data) < 2: return {"total": 0, "done": 0, "in_progress": 0}
        total = len(data) - 1
        done = sum(1 for row in data if "🏁 ЗАВЕРШЕН" in row)
        in_p = sum(1 for row in data if "🚕 В ПУТИ" in row)
        return {"total": total, "done": done, "in_progress": in_p}
    except:
        return {"total": 0, "done": 0, "in_progress": 0}