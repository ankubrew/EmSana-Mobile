from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from fastapi.responses import HTMLResponse

# --- НАСТРОЙКИ SUPABASE ---
SUPABASE_URL = "https://ezhetuwzvcuynhzdgflk.supabase.co"
SUPABASE_KEY = "sb_publishable_wWTgfp7z7IypTS4D6U7c8g_UYdPEsme"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
app = FastAPI()

class UserAuth(BaseModel):
    email: str
    password: str

# Глобальная переменная для связи браузера и приложения
is_google_logged_in = False 

@app.post("/register")
def register_user(user: UserAuth):
    try:
        supabase.auth.sign_up({"email": user.email, "password": user.password})
        return {"message": "Успешная регистрация!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login")
def login_user(user: UserAuth):
    try:
        supabase.auth.sign_in_with_password({"email": user.email, "password": user.password})
        return {"message": "Успешный вход!"}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Неверный email или пароль!")

@app.get("/auth/google")
def login_google():
    global is_google_logged_in
    is_google_logged_in = False
    
    try:
        res = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"redirect_to": "http://127.0.0.1:8000/callback"}
        })
        return {"url": res.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# МАГИЧЕСКИЙ МОСТ: Браузер говорит серверу, что всё ок
@app.get("/callback", response_class=HTMLResponse)
def auth_callback():
    return """
    <html>
        <body style="display:flex; justify-content:center; align-items:center; height:100vh; font-family:sans-serif; background-color:#121212; color:white;">
            <div style="text-align:center;">
                <h1 style="color: #4CAF50;">Вход выполнен успешно! 🎉</h1>
                <p>Теперь вы можете закрыть это окно. Приложение EmSana обновится автоматически.</p>
            </div>
            <script>
                // Тот самый скрипт, которого у тебя не хватало!
                fetch('http://127.0.0.1:8000/google-success', {method: 'POST'});
            </script>
        </body>
    </html>
    """

@app.post("/google-success")
def google_success():
    global is_google_logged_in
    is_google_logged_in = True
    return {"status": "ok"}

# FLET спрашивает у сервера, всё ли ок
@app.get("/check-google")
def check_google():
    global is_google_logged_in
    if is_google_logged_in:
        is_google_logged_in = False 
        return {"status": "success"}
    return {"status": "waiting"}