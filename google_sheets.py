import os
import gspread
from google.oauth2.service_account import Credentials

# Настройки путей
base_path = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(base_path, 'credentials.json')

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Авторизация
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

SPREADSHEET_NAME = 'Obor-bot-orders'
sheet = client.open(SPREADSHEET_NAME).sheet1


def append_order(order_data: dict):
    """Добавляет новый заказ в таблицу"""
    row = [
        order_data.get('order_id', ''),
        order_data.get('time', ''),
        order_data.get('first_name', ''),
        order_data.get('phone', ''),
        order_data.get('items', ''),
        order_data.get('status', '🆕 НОВЫЙ')
    ]
    sheet.append_row(row)


def update_order_status(order_id: str, new_status: str):
    """Обновляет статус заказа по его ID"""
    try:
        cell = sheet.find(str(order_id))
        sheet.update_cell(cell.row, 6, new_status)  # Статус в 6-й колонке
        return True
    except:
        return False


def get_stats():
    """Считает статистику из таблицы"""
    try:
        # Получаем все значения (включая те, что без заголовков)
        data = sheet.get_all_values()
        if not data:
            return {"total": 0, "done": 0, "in_progress": 0}

        total = len(data) - 1  # Вычитаем заголовок
        done = sum(1 for row in data if "🏁 ЗАВЕРШЕН" in row)

        return {
            "total": max(0, total),
            "done": done,
            "in_progress": max(0, total - done)
        }
    except Exception as e:
        print(f"Ошибка статистики: {e}")
        return {"total": 0, "done": 0, "in_progress": 0}