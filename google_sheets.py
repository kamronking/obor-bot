import os
import json
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def get_creds():
    # 1. Проверка переменной окружения (для Render)
    creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if creds_json:
        try:
            return Credentials.from_service_account_info(json.loads(creds_json), scopes=SCOPES)
        except Exception as e:
            print(f"❌ Ошибка в GOOGLE_CREDENTIALS_JSON: {e}")

    # 2. Проверка файла (локально на MacBook)
    base_path = os.path.dirname(os.path.abspath(__file__))

    # Проверяем оба варианта названия (с пробелом и без)
    possible_files = ['credentials.json', 'credentials .json']

    for file_name in possible_files:
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
        SPREADSHEET_NAME = 'Obor-bot-orders'
        sheet = client.open(SPREADSHEET_NAME).sheet1
        print("✅ Подключение к Google Таблицам установлено")
    else:
        print("⚠️ Ключи Google не найдены!")
        sheet = None
except Exception as e:
    print(f"🚨 Ошибка авторизации: {e}")
    sheet = None

# Далее идут твои функции (append_order, get_stats и т.д.) без изменений