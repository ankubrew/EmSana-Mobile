import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from fastapi.responses import HTMLResponse
from typing import Optional
from dotenv import load_dotenv

# Secret Key
load_dotenv()
SUPABASE_URL = "https://ezhetuwzvcuynhzdgflk.supabase.co"
SUPABASE_KEY = "sb_publishable_wWTgfp7z7IypTS4D6U7c8g_UYdPEsme"

# Инициализация обычного клиента
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Подтягиваем Secret Key из .env для админ-функций
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_SERVICE_KEY:
    print("❌ Ошибка: SUPABASE_SERVICE_KEY не найден в .env файле!")

# Админ-клиент для сброса паролей
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY) if SUPABASE_SERVICE_KEY else None

app = FastAPI()

class UserAuth(BaseModel):
    email: str
    password: str

class TokenReceiver(BaseModel):
    access_token: Optional[str] = None

class VerifyToken(BaseModel):
    access_token: str

class PasswordResetRequest(BaseModel):
    email: str

class PasswordUpdate(BaseModel):
    access_token: str
    new_password: str

google_auth_state = {
    "status": "waiting",
    "access_token": None
}

@app.post("/register")
def register_user(user: UserAuth):
    try:
        response = supabase.auth.sign_up({"email": user.email, "password": user.password})
        # Supabase returns an identities array; if empty, user already exists
        if response.user and len(response.user.identities) == 0:
            raise HTTPException(status_code=400, detail="User already registered")
        return {"message": "Confirmation email sent! Please check your inbox."}
    except HTTPException:
        raise
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


@app.post("/forgot-password")
def forgot_password(data: PasswordResetRequest):
    try:
        supabase.auth.reset_password_email(
            data.email,
            options={"redirect_to": "http://127.0.0.1:8000/reset-password"}
        )
        return {"message": "Password reset email sent."}
    except Exception as e:
        # Always return success to avoid email enumeration
        return {"message": "If that email exists, a reset link has been sent."}


@app.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(access_token: Optional[str] = None, token_hash: Optional[str] = None, type: Optional[str] = None):
    return """
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                * { box-sizing: border-box; margin: 0; padding: 0; }
                body {
                    font-family: 'Inter', -apple-system, sans-serif;
                    background: #FFFFFF;
                    display: flex; justify-content: center; align-items: center;
                    min-height: 100vh;
                }
                .card {
                    max-width: 380px; width: 100%; padding: 40px;
                    text-align: center;
                }
                h2 { font-size: 22px; font-weight: 600; color: #000; margin-bottom: 24px; }
                input {
                    width: 100%; padding: 12px 0; font-size: 15px;
                    border: none; border-bottom: 1px solid #E0E0E0;
                    outline: none; margin-bottom: 20px; color: #000;
                }
                input:focus { border-bottom-color: #000; }
                button {
                    width: 100%; padding: 14px; font-size: 15px; font-weight: 600;
                    background: #000; color: #FFF; border: none; border-radius: 6px;
                    cursor: pointer;
                }
                button:hover { background: #333; }
                #msg { margin-top: 16px; font-size: 14px; }
                .success { color: #4CAF50; }
                .error { color: #D32F2F; }
            </style>
        </head>
        <body>
            <div class="card">
                <h2>Set new password</h2>
                <input type="password" id="pw" placeholder="New password (min. 6 chars)" />
                <button onclick="resetPw()">Update password</button>
                <p id="msg"></p>
            </div>
            <script>
                const hash = window.location.hash.substring(1);
                const params = new URLSearchParams(hash);
                const accessToken = params.get('access_token');

                async function resetPw() {
                    const pw = document.getElementById('pw').value;
                    if (pw.length < 6) {
                        document.getElementById('msg').className = 'error';
                        document.getElementById('msg').innerText = 'Password must be at least 6 characters.';
                        return;
                    }
                    const res = await fetch('http://127.0.0.1:8000/update-password', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({access_token: accessToken, new_password: pw})
                    });
                    const data = await res.json();
                    if (res.ok) {
                        document.getElementById('msg').className = 'success';
                        document.getElementById('msg').innerText = 'Password updated! You can close this tab and log in.';
                    } else {
                        document.getElementById('msg').className = 'error';
                        document.getElementById('msg').innerText = data.detail || 'Something went wrong.';
                    }
                }
            </script>
        </body>
    </html>
    """


@app.post("/update-password")
def update_password(data: PasswordUpdate):
    try:
        user = supabase.auth.get_user(data.access_token)
        supabase_admin.auth.admin.update_user_by_id(
            user.user.id,
            {"password": data.new_password}
        )
        return {"message": "Password updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/email-confirmed", response_class=HTMLResponse)
def email_confirmed():
    return """
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
        <body style="font-family: 'Inter', sans-serif; background: #FFF; display: flex;
                     justify-content: center; align-items: center; min-height: 100vh;
                     text-align: center;">
            <div>
                <h2 style="font-size: 22px; color: #000;">Email confirmed ✓</h2>
                <p style="color: #666; margin-top: 12px;">
                    Your account is verified. You can now open EmSana and log in.
                </p>
            </div>
        </body>
    </html>
    """