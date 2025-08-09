import gspread
from google.oauth2.service_account import Credentials

SERVICE_ACCOUNT_FILE = 'telegram-bot-orders-468421-dd17fe6e9c16.json'  # укажи свой путь сюда
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

SPREADSHEET_NAME = 'Obor-bot-orders'  # имя твоей Google Sheets таблицы
sheet = client.open(SPREADSHEET_NAME).sheet1


def append_order(order_data: dict):
    row = [
        order_data.get('time', ''),
        order_data.get('user_id', ''),
        order_data.get('username', ''),
        order_data.get('first_name', ''),
        order_data.get('phone', ''),
        order_data.get('items', ''),
    ]
    sheet.append_row(row)
    #print("added to google sheet")


if __name__ == "__main__":
    test_order = {
        "time": "2025-08-09 10:00:00",
        "user_id": 123456,
        "username": "testuser",
        "first_name": "Kamron",
        "phone": "+998901234567",
        "items": "Test source | Test what",
    }
    append_order(test_order)
