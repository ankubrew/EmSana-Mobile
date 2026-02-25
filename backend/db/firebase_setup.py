import firebase_admin
from firebase_admin import credentials, auth

# Указываем путь к твоему ключу (относительно корня папки backend)
CREDENTIALS_PATH = "db/firebase-key.json"

def initialize_firebase():
    """Инициализация защищенного подключения к Firebase"""
    try:
        # Проверяем, не запущено ли уже подключение (важно для FastAPI)
        if not firebase_admin._apps:
            cred = credentials.Certificate(CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            print("✅ Успешное подключение к Firebase Admin SDK!")
    except Exception as e:
        print(f"❌ Ошибка подключения к Firebase: {e}")

# Запускаем функцию при запуске бэкенда
initialize_firebase()