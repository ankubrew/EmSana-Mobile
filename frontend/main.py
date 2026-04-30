import flet as ft
import requests
import time
import threading 

def main(page: ft.Page):
    page.title = "EmSana"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#FFFFFF"
    page.padding = 0

    is_login = ft.Ref[bool]()
    is_login.current = False 

    email_input = ft.TextField(
        label="EMAIL",
        label_style=ft.TextStyle(
            size=11,
            weight=ft.FontWeight.W_500,
            color="#999999",
            letter_spacing=1.5,
        ),
        width=340,
        height=55,
        border=ft.InputBorder.UNDERLINE,
        border_color="#E0E0E0",
        focused_border_color="#000000",
        cursor_color="#000000",
        color="#000000",
        text_size=15,
        content_padding=ft.padding.only(left=0, top=20, bottom=8),
    )

    password_input = ft.TextField(
        label="PASSWORD",
        label_style=ft.TextStyle(
            size=11,
            weight=ft.FontWeight.W_500,
            color="#999999",
            letter_spacing=1.5,
        ),
        password=True,
        can_reveal_password=True,
        width=340,
        height=55,
        border=ft.InputBorder.UNDERLINE,
        border_color="#E0E0E0",
        focused_border_color="#000000",
        cursor_color="#000000",
        color="#000000",
        text_size=15,
        content_padding=ft.padding.only(left=0, top=20, bottom=8),
    )
    status_text = ft.Text(value="", size=13, color="#D32F2F", weight=ft.FontWeight.W_400)

    def wipe_data():
        page.client_storage.remove("access_token")
        page.client_storage.remove("parent_pin")
        page.client_storage.remove("parent_name")
        page.client_storage.remove("child_name")

    def lock_auth_ui(locked: bool):
        email_input.disabled = locked
        password_input.disabled = locked
        main_btn.disabled = locked
        google_btn.disabled = locked
        toggle_btn.disabled = locked
        page.update()

    def check_session_on_startup():
        page.clean()
        page.add(
            ft.ProgressRing(color=ft.Colors.BLUE_400),
            ft.Container(height=10),
            ft.Text("Проверка безопасности...", color=ft.Colors.GREY_400)
        )
        page.update()

        saved_token = page.client_storage.get("access_token")
        
        if saved_token:
            try:
                res = requests.post("http://127.0.0.1:8000/verify-session", json={"access_token": saved_token})
                if res.status_code == 200 and res.json().get("valid") == True:
                    if page.client_storage.contains_key("parent_pin"):
                        show_main_scene()
                    else:
                        show_onboarding_scene()
                    return
                else:
                    wipe_data() 
            except Exception as e:
                print("Бэкенд недоступен:", e)
        
        wipe_data() 
        show_auth_scene()

    def show_onboarding_scene():
        page.clean()
        page.bgcolor = "#0B0C10"

        def cancel_onboarding(e):
            wipe_data() 
            show_auth_scene()

        back_btn = ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE, on_click=cancel_onboarding)], alignment=ft.MainAxisAlignment.START)
        parent_name_input = ft.TextField(label="Ваше имя (Родитель)", width=250, text_align=ft.TextAlign.CENTER)
        child_name_input = ft.TextField(label="Имя ребенка", width=250, text_align=ft.TextAlign.CENTER)
        new_pin_input = ft.TextField(label="Придумайте 4-значный ПИН-код", password=True, can_reveal_password=True, width=250, text_align=ft.TextAlign.CENTER, keyboard_type=ft.KeyboardType.NUMBER, max_length=4)
        onboard_error = ft.Text("", color=ft.Colors.RED)

        def save_onboarding_data(e):
            if not parent_name_input.value or not child_name_input.value:
                onboard_error.value = "Пожалуйста, введите имена!"
                page.update()
                return

            if len(new_pin_input.value) == 4 and new_pin_input.value.isdigit():
                page.client_storage.set("parent_pin", new_pin_input.value) 
                page.client_storage.set("parent_name", parent_name_input.value)
                page.client_storage.set("child_name", child_name_input.value)
                show_main_scene() 
            else:
                onboard_error.value = "ПИН-код должен состоять из 4 цифр!"
                page.update()

        page.add(
            back_btn,
            ft.Container(height=10),
            ft.Row([ft.Icon(ft.Icons.ROCKET_LAUNCH, size=50, color=ft.Colors.BLUE_400)], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([ft.Text("Добро пожаловать в EmSana!", size=30, weight="bold", color=ft.Colors.WHITE)], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([ft.Text("Давайте настроим профили.", color=ft.Colors.GREY_400)], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=20),
            ft.Row([parent_name_input], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([child_name_input], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([new_pin_input], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([onboard_error], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=10),
            ft.Row([ft.ElevatedButton("Сохранить и начать", bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE, on_click=save_onboarding_data)], alignment=ft.MainAxisAlignment.CENTER)
        )
        page.update()

    def show_main_scene():
        page.clean()
        page.bgcolor = "#0B0C10"

        p_name = page.client_storage.get("parent_name") or "Родитель"
        c_name = page.client_storage.get("child_name") or "Ребенок"

        def go_to_child_space(e):
            page.clean()
            page.add(
                ft.Text(f"🚀 Космос ({c_name})", size=30, color=ft.Colors.WHITE),
                ft.ElevatedButton("Выйти в меню", on_click=lambda _: show_main_scene())
            )
            page.update()

        def go_to_parent_dashboard():
            page.clean()

            def logout(e):
                page.client_storage.remove("access_token") 
                show_auth_scene()

            page.add(
                ft.Text(f"📊 Панель управления ({p_name})", size=30, color=ft.Colors.WHITE),
                ft.Container(height=20),
                ft.ElevatedButton("Назад к профилям", on_click=lambda _: show_main_scene()),
                ft.ElevatedButton("Выйти из аккаунта", bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, on_click=logout)
            )
            page.update()

        # ИСПРАВЛЕННЫЙ УЧАСТОК КОДА (С ограничением в 4 символа)
        pin_input = ft.TextField(
            label="Введите ПИН-код", password=True, can_reveal_password=True, 
            width=200, text_align=ft.TextAlign.CENTER, keyboard_type=ft.KeyboardType.NUMBER,
            max_length=4
        )
        pin_error = ft.Text("", color=ft.Colors.RED)

        def check_pin(e):
            if pin_input.value == page.client_storage.get("parent_pin"): 
                go_to_parent_dashboard()
            else:
                pin_error.value = "Неверный ПИН-код!"
                pin_input.value = ""
                page.update()

        def show_pin_dialog(e):
            page.clean()
            page.add(
                ft.Container(height=80),
                ft.Row([ft.Icon(ft.Icons.LOCK, size=50, color=ft.Colors.WHITE)], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([ft.Text(f"Доступ для {p_name}", size=25, color=ft.Colors.WHITE)], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=20),
                ft.Row([pin_input], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([pin_error], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=20),
                ft.Row([
                    ft.ElevatedButton("Отмена", on_click=lambda _: show_main_scene()),
                    ft.ElevatedButton("Войти", bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE, on_click=check_pin)
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
            )
            page.update()

        parent_card = ft.Container(
            content=ft.Column([ft.Icon(ft.Icons.PERSON, size=80, color=ft.Colors.WHITE), ft.Text(p_name, size=20, color=ft.Colors.WHITE)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=200, height=250, border_radius=20, border=ft.border.all(1, ft.Colors.GREY_400), ink=True, on_click=show_pin_dialog 
        )

        child_card = ft.Container(
            content=ft.Column([ft.Icon(ft.Icons.ROCKET_LAUNCH, size=80, color=ft.Colors.WHITE), ft.Text(c_name, size=20, color=ft.Colors.WHITE)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=200, height=250, border_radius=20, border=ft.border.all(1, ft.Colors.GREY_400), ink=True, on_click=go_to_child_space
        )

        page.add(
            ft.Container(height=50),
            ft.Row([ft.Text("Кто сейчас пользуется EmSana?", size=30, color=ft.Colors.WHITE)], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=40),
            ft.Row([parent_card, child_card], alignment=ft.MainAxisAlignment.CENTER, spacing=50)
        )
        page.update()

    def execute_login(access_token):
        if access_token:
            page.client_storage.set("access_token", access_token) 
        if page.client_storage.contains_key("parent_pin"):
            show_main_scene() 
        else:
            show_onboarding_scene() 

    def auth_google(e):
        lock_auth_ui(True) 
        status_text.value = "🚀 Запуск авторизации..."
        status_text.color = ft.Colors.BLUE_400
        page.update()
        try:
            res = requests.get("http://127.0.0.1:8000/auth/google")
            if res.status_code == 200:
                page.launch_url(res.json().get("url")) 
                status_text.value = "⏳ Ожидание входа в браузере..."
                page.update()

                def check_login():
                    success = False
                    for i in range(60): 
                        time.sleep(1)
                        try:
                            check_res = requests.get("http://127.0.0.1:8000/check-google")
                            data = check_res.json()
                            if data.get("status") == "success":
                                execute_login(data.get("access_token")) 
                                success = True
                                break
                        except Exception as err: 
                            print(f"Ошибка шпиона: {err}")
                    
                    if not success:
                        status_text.value = "Время ожидания истекло. Попробуйте еще раз."
                        status_text.color = ft.Colors.RED
                        lock_auth_ui(False)

                threading.Thread(target=check_login, daemon=True).start()
            else:
                status_text.value = "Ошибка сервера"
                status_text.color = ft.Colors.RED
                lock_auth_ui(False)
        except Exception as ex:
            print(f"ОШИБКА: {ex}")
            status_text.value = "Ошибка соединения (Проверь uvicorn!)"
            status_text.color = ft.Colors.RED
            lock_auth_ui(False)

    def handle_auth(e):
        if not email_input.value or not password_input.value:
            status_text.value = "Пожалуйста, введите Email и Пароль!"
            status_text.color = ft.Colors.RED
            page.update()
            return

        lock_auth_ui(True) 
        endpoint = "/login" if is_login.current else "/register"
        status_text.value = "Загрузка..."
        status_text.color = ft.Colors.WHITE
        page.update()
        try:
            res = requests.post(
                f"http://127.0.0.1:8000{endpoint}",
                json={"email": email_input.value, "password": password_input.value}
            )
            data = res.json()
            if res.status_code == 200:
                if endpoint == "/login":
                    execute_login(data.get("access_token")) 
                else:
                    show_email_confirmation_pending_scene()
                    return
            else:
                raw_error = data.get('detail')
                error_dict = {
                    "User already registered": "Account already exists. Please log in.",
                    "Invalid login credentials": "Invalid email or password.",
                    "Password should be at least 6 characters.": "Password must be at least 6 characters.",
                    "Email not confirmed": "Please confirm your email before logging in.",
                }
                status_text.value = f"Ошибка: {error_dict.get(raw_error, raw_error)}"
                status_text.color = ft.Colors.RED
                lock_auth_ui(False)
        except Exception as ex: 
            print(f"ОШИБКА: {ex}")
            status_text.value = "Ошибка: сервер не отвечает"
            status_text.color = ft.Colors.RED
            lock_auth_ui(False)

    def toggle_mode(e):
        is_login.current = not is_login.current
        show_auth_scene()

    title_text = ft.Text(
        "Sign in to EmSana",
        size=28,
        weight=ft.FontWeight.BOLD,
        color="#000000",
        font_family="Inter",
    )
    main_btn = ft.ElevatedButton(
        text="Log in",
        width=340,
        height=48,
        on_click=handle_auth,
        bgcolor="#000000",
        color="#FFFFFF",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=6),
            text_style=ft.TextStyle(size=15, weight=ft.FontWeight.W_600),
        ),
    )
    google_btn = ft.OutlinedButton(
        content=ft.Row(
            [
                ft.Image(
                    src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg",
                    width=18,
                    height=18,
                ),
                ft.Text("Continue with Google", color="#000000", size=14, weight=ft.FontWeight.W_500),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        ),
        width=340,
        height=48,
        on_click=auth_google,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=6),
            side=ft.BorderSide(1, "#E0E0E0"),
        ),
    )
    toggle_btn = ft.TextButton(
        "No account? Create one",
        on_click=toggle_mode,
        style=ft.ButtonStyle(
            color="#6C63FF",
        ),
    )
    forgot_password_btn = ft.TextButton(
        "Forgot password?",
        on_click=lambda e: show_forgot_password_scene(),
        style=ft.ButtonStyle(
            color="#6C63FF",
        ),
    )

    def show_forgot_password_scene():
        page.clean()
        page.bgcolor = "#FFFFFF"

        fp_email = ft.TextField(
            label="EMAIL",
            label_style=ft.TextStyle(size=11, weight=ft.FontWeight.W_500, color="#999999", letter_spacing=1.5),
            width=340,
            height=55,
            border=ft.InputBorder.UNDERLINE,
            border_color="#E0E0E0",
            focused_border_color="#000000",
            cursor_color="#000000",
            color="#000000",
            text_size=15,
            content_padding=ft.padding.only(left=0, top=20, bottom=8),
        )
        fp_status = ft.Text("", size=13)

        def send_reset(e):
            if not fp_email.value:
                fp_status.value = "Please enter your email."
                fp_status.color = "#D32F2F"
                page.update()
                return
            try:
                res = requests.post(
                    "http://127.0.0.1:8000/forgot-password",
                    json={"email": fp_email.value},
                )
                fp_status.value = "If that email exists, a reset link has been sent."
                fp_status.color = "#4CAF50"
            except Exception:
                fp_status.value = "Server is unreachable."
                fp_status.color = "#D32F2F"
            page.update()

        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Reset password", size=28, weight=ft.FontWeight.BOLD, color="#000000"),
                        ft.Container(height=8),
                        ft.Text(
                            "Enter your email and we'll send you a link to reset your password.",
                            size=14,
                            color="#666666",
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=24),
                        fp_email,
                        ft.Container(height=20),
                        ft.ElevatedButton(
                            text="Send reset link",
                            width=340,
                            height=48,
                            bgcolor="#000000",
                            color="#FFFFFF",
                            on_click=send_reset,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=6),
                                text_style=ft.TextStyle(size=15, weight=ft.FontWeight.W_600),
                            ),
                        ),
                        ft.Container(height=16),
                        fp_status,
                        ft.Container(height=12),
                        ft.TextButton(
                            "← Back to login",
                            on_click=lambda e: show_auth_scene(),
                            style=ft.ButtonStyle(color="#6C63FF"),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                ),
                alignment=ft.alignment.center,
                padding=ft.padding.symmetric(horizontal=40),
                expand=True,
            )
        )
        page.update()

    def show_email_confirmation_pending_scene():
        page.clean()
        page.bgcolor = "#FFFFFF"

        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.MARK_EMAIL_READ_OUTLINED, size=56, color="#6C63FF"),
                        ft.Container(height=16),
                        ft.Text("Check your email", size=28, weight=ft.FontWeight.BOLD, color="#000000"),
                        ft.Container(height=8),
                        ft.Text(
                            "We sent a confirmation link to your email.\nClick it to activate your account.",
                            size=14,
                            color="#666666",
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=32),
                        ft.TextButton(
                            "← Back to login",
                            on_click=lambda e: show_auth_scene(),
                            style=ft.ButtonStyle(color="#6C63FF"),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                ),
                alignment=ft.alignment.center,
                padding=ft.padding.symmetric(horizontal=40),
                expand=True,
            )
        )
        page.update()

    def show_auth_scene():
        email_input.value = ""
        password_input.value = ""
        status_text.value = ""
        lock_auth_ui(False)

        # Update button/title text based on mode
        if is_login.current:
            title_text.value = "Sign in to EmSana"
            main_btn.text = "Log in"
            toggle_btn.text = "No account? Create one"
        else:
            title_text.value = "Create an account"
            main_btn.text = "Create account"
            toggle_btn.text = "Already have an account? Log in"

        page.clean()
        page.bgcolor = "#FFFFFF"
        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        title_text,
                        ft.Container(height=24),
                        google_btn,
                        ft.Container(height=16),
                        ft.Row(
                            [
                                ft.Container(
                                    bgcolor="#E0E0E0", height=1, expand=True
                                ),
                                ft.Text(
                                    "  or  ",
                                    size=13,
                                    color="#999999",
                                    weight=ft.FontWeight.W_400,
                                ),
                                ft.Container(
                                    bgcolor="#E0E0E0", height=1, expand=True
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            width=340,
                        ),
                        ft.Container(height=16),
                        email_input,
                        ft.Container(height=4),
                        password_input,
                        ft.Container(height=20),
                        main_btn,
                        ft.Container(height=12),
                        forgot_password_btn if is_login.current else ft.Container(),
                        toggle_btn,
                        ft.Container(height=8),
                        status_text,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                ),
                alignment=ft.alignment.center,
                padding=ft.padding.symmetric(horizontal=40),
                expand=True,
            )
        )
        page.update()

    check_session_on_startup()

ft.app(target=main)