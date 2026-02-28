from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from fastapi.responses import HTMLResponse
from typing import Optional

SUPABASE_URL = "https://ezhetuwzvcuynhzdgflk.supabase.co"
SUPABASE_KEY = "sb_publishable_wWTgfp7z7IypTS4D6U7c8g_UYdPEsme"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
app = FastAPI()

class UserAuth(BaseModel):
    email: str
    password: str

class TokenReceiver(BaseModel):
    access_token: Optional[str] = None

class VerifyToken(BaseModel):
    access_token: str

google_auth_state = {
    "status": "waiting",
    "access_token": None
}

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
        response = supabase.auth.sign_in_with_password({"email": user.email, "password": user.password})
        return {"message": "Успешный вход!", "access_token": response.session.access_token}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Неверный email или пароль!")

@app.get("/auth/google")
def login_google():
    global google_auth_state
    google_auth_state = {"status": "waiting", "access_token": None} 
    try:
        res = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"redirect_to": "http://127.0.0.1:8000/callback"}
        })
        return {"url": res.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# УНИВЕРСАЛЬНЫЙ МОСТ (Ловит и code, и access_token)
@app.get("/callback", response_class=HTMLResponse)
def auth_callback(code: Optional[str] = None):
    global google_auth_state
    
    # Если Гугл прислал код напрямую
    if code:
        try:
            res = supabase.auth.exchange_code_for_session({"auth_code": code})
            google_auth_state = {"status": "success", "access_token": res.session.access_token}
            return "<html><body style='background:#121212; color:#4CAF50; text-align:center; padding-top:20%; font-family:sans-serif;'><h1>Вход выполнен успешно! 🎉</h1><p>Можете закрыть окно.</p></body></html>"
        except Exception as e:
            pass

    # Если Гугл спрятал токен в хэш браузера (Запасной план)
    return """
    <html>
        <body style="background:#121212; color:white; text-align:center; padding-top:20%; font-family:sans-serif;">
            <h2 id="msg">Завершение входа... 🔄</h2>
            <script>
                const hash = window.location.hash.substring(1);
                const params = new URLSearchParams(hash);
                const token = params.get('access_token');
                
                if (token) {
                    fetch('http://127.0.0.1:8000/google-success', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({access_token: token})
                    }).then(() => {
                        document.getElementById("msg").innerHTML = "<span style='color:#4CAF50;'>Вход выполнен успешно! 🎉</span><br><br>Можете закрыть это окно.";
                    });
                } else {
                    document.getElementById("msg").innerHTML = "<span style='color:red;'>Ошибка: Гугл не вернул данные!</span>";
                }
            </script>
        </body>
    </html>
    """

@app.post("/google-success")
def google_success(data: TokenReceiver):
    global google_auth_state
    if data.access_token:
        google_auth_state = {"status": "success", "access_token": data.access_token}
    return {"status": "ok"}

@app.get("/check-google")
def check_google():
    global google_auth_state
    if google_auth_state["status"] == "success":
        res = dict(google_auth_state)
        google_auth_state = {"status": "waiting", "access_token": None}
        return res
    return {"status": "waiting"}

@app.post("/verify-session")
def verify_session(data: VerifyToken):
    try:
        response = supabase.auth.get_user(data.access_token)
        if response.user:
            return {"valid": True}
        return {"valid": False}
    except Exception as e:
        return {"valid": False, "error": str(e)}