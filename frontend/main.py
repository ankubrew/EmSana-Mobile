import flet as ft
import requests
import time
import threading 

def main(page: ft.Page):
    page.title = "EmSana"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0B0C10"

    is_login = ft.Ref[bool]()
    is_login.current = False 

    email_input = ft.TextField(label="Email", width=300, border_radius=10)
    password_input = ft.TextField(label="Пароль", password=True, can_reveal_password=True, width=300, border_radius=10)
    status_text = ft.Text(value="", size=14, color=ft.Colors.RED)

    # ==========================================
    # 1. ЭКРАН ОНБОРДИНГА (ИМЕНА + ПИН-КОД)
    # ==========================================
    def show_onboarding_scene():
        page.clean()
        page.bgcolor = "#0B0C10"

        parent_name_input = ft.TextField(label="Ваше имя (Родитель)", width=250, text_align=ft.TextAlign.CENTER)
        child_name_input = ft.TextField(label="Имя ребенка", width=250, text_align=ft.TextAlign.CENTER)
        
        new_pin_input = ft.TextField(
            label="Придумайте 4-значный ПИН-код", 
            password=True, can_reveal_password=True, 
            width=250, text_align=ft.TextAlign.CENTER, 
            keyboard_type=ft.KeyboardType.NUMBER,
            max_length=4 
        )
        onboard_error = ft.Text("", color=ft.Colors.RED)

        def save_onboarding_data(e):
            if not parent_name_input.value or not child_name_input.value:
                onboard_error.value = "Пожалуйста, введите имена!"
                page.update()
                return

            if len(new_pin_input.value) == 4 and new_pin_input.value.isdigit():
                # Сохраняем ВСЁ в локальную базу устройства
                page.client_storage.set("parent_pin", new_pin_input.value) 
                page.client_storage.set("parent_name", parent_name_input.value)
                page.client_storage.set("child_name", child_name_input.value)
                show_main_scene() 
            else:
                onboard_error.value = "ПИН-код должен состоять из 4 цифр!"
                page.update()

        page.add(
            ft.Container(height=40),
            ft.Icon(ft.Icons.ROCKET_LAUNCH, size=50, color=ft.Colors.BLUE_400),
            ft.Text("Добро пожаловать в EmSana!", size=30, weight="bold", color=ft.Colors.WHITE),
            ft.Text("Давайте настроим профили для вас и ребенка.", color=ft.Colors.GREY_400),
            ft.Container(height=20),
            parent_name_input,
            child_name_input,
            new_pin_input,
            onboard_error,
            ft.Container(height=10),
            ft.ElevatedButton("Сохранить и начать", bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE, on_click=save_onboarding_data)
        )
        page.update()

    # ==========================================
    # 2. ГЛАВНЫЙ ЭКРАН (КАРТОЧКИ ПРОФИЛЕЙ)
    # ==========================================
    def show_main_scene():
        page.clean()
        page.bgcolor = "#0B0C10"

        # Достаем имена из базы
        p_name = page.client_storage.get("parent_name") or "Родитель"
        c_name = page.client_storage.get("child_name") or "Ребенок"

        # --- Космос Ребенка ---
        def go_to_child_space(e):
            page.clean()
            page.add(
                ft.Text(f"🚀 Космос ({c_name})", size=30, color=ft.Colors.WHITE),
                ft.ElevatedButton("Выйти в меню", on_click=lambda _: show_main_scene())
            )
            page.update()

        # --- Панель Родителя ---
        def go_to_parent_dashboard():
            page.clean()

            def logout(e):
                page.client_storage.clear() # Полная очистка
                page.clean()
                page.add(
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=60),
                    ft.Text("Вы успешно вышли!", size=20, color=ft.Colors.WHITE),
                    ft.ElevatedButton("К экрану входа", on_click=lambda _: page.window_destroy()) # Или просто перезапуск
                )
                page.update()

            page.add(
                ft.Text(f"📊 Панель управления ({p_name})", size=30, color=ft.Colors.WHITE),
                ft.Container(height=20),
                ft.ElevatedButton("Назад к профилям", on_click=lambda _: show_main_scene()),
                ft.ElevatedButton("Выйти из аккаунта", bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, on_click=logout)
            )
            page.update()

        # --- Логика ПИН-кода ---
        pin_input = ft.TextField(
            label="Введите ПИН-код", password=True, can_reveal_password=True, 
            width=200, text_align=ft.TextAlign.CENTER, keyboard_type=ft.KeyboardType.NUMBER
        )
        pin_error = ft.Text("", color=ft.Colors.RED)

        def check_pin(e):
            saved_pin = page.client_storage.get("parent_pin")
            if pin_input.value == saved_pin: 
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

        # --- Карточки ---
        parent_card = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.PERSON, size=80, color=ft.Colors.WHITE),
                ft.Text(p_name, size=20, color=ft.Colors.WHITE)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=200, height=250, border_radius=20, border=ft.border.all(1, ft.Colors.GREY_400),
            ink=True, on_click=show_pin_dialog 
        )

        child_card = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.ROCKET_LAUNCH, size=80, color=ft.Colors.WHITE),
                ft.Text(c_name, size=20, color=ft.Colors.WHITE)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=200, height=250, border_radius=20, border=ft.border.all(1, ft.Colors.GREY_400),
            ink=True, on_click=go_to_child_space
        )

        page.add(
            ft.Container(height=50),
            ft.Row([ft.Text("Кто сейчас пользуется EmSana?", size=30, color=ft.Colors.WHITE)], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=40),
            ft.Row([parent_card, child_card], alignment=ft.MainAxisAlignment.CENTER, spacing=50)
        )
        page.update()

    # ==========================================
    # 3. ФУНКЦИИ ВХОДА И МАРШРУТИЗАЦИЯ
    # ==========================================
    def navigate_after_login():
        if page.client_storage.contains_key("parent_pin"):
            show_main_scene() 
        else:
            show_onboarding_scene() 

    def auth_google(e):
        status_text.value = "🚀 Запуск авторизации..."
        status_text.color = ft.Colors.BLUE_400
        page.update()
        try:
            res = requests.get("http://127.0.0.1:8000/auth/google")
            if res.status_code == 200:
                google_url = res.json().get("url")
                page.launch_url(google_url) 
                status_text.value = "⏳ Ожидание входа в браузере..."
                page.update()

                def check_login():
                    for i in range(60): 
                        time.sleep(1)
                        try:
                            check_res = requests.get("http://127.0.0.1:8000/check-google")
                            if check_res.json().get("status") == "success":
                                navigate_after_login() 
                                break
                        except: pass
                threading.Thread(target=check_login, daemon=True).start()
            else:
                status_text.value = "Ошибка сервера"
                status_text.color = ft.Colors.RED
        except:
            status_text.value = "Ошибка соединения (Проверь uvicorn!)"
            status_text.color = ft.Colors.RED
        page.update()

    def handle_auth(e):
        endpoint = "/login" if is_login.current else "/register"
        status_text.value = "Загрузка..."
        status_text.color = ft.Colors.WHITE
        page.update()
        try:
            res = requests.post(
                f"http://127.0.0.1:8000{endpoint}",
                json={"email": email_input.value, "password": password_input.value}
            )
            if res.status_code == 200:
                navigate_after_login() 
            else:
                raw_error = res.json().get('detail')
                error_dict = {
                    "User already registered": "Аккаунт уже есть. Нажмите 'Войти'",
                    "Invalid login credentials": "Неверный Email или пароль!",
                    "Password should be at least 6 characters.": "Пароль слишком короткий",
                }
                translated_error = error_dict.get(raw_error, raw_error) 
                status_text.value = f"Ошибка: {translated_error}"
                status_text.color = ft.Colors.RED
        except:
            status_text.value = "Ошибка: сервер FastAPI не запущен"
            status_text.color = ft.Colors.RED
        page.update()

    def toggle_mode(e):
        is_login.current = not is_login.current
        title_text.value = "Вход в EmSana" if is_login.current else "Регистрация в EmSana"
        main_btn.text = "Войти" if is_login.current else "Создать аккаунт"
        toggle_btn.text = "Нет аккаунта? Регистрация" if is_login.current else "Уже есть аккаунт? Войти"
        status_text.value = ""
        page.update()

    # --- Начальный экран входа ---
    title_text = ft.Text("Регистрация в EmSana", size=35, weight="bold")
    main_btn = ft.ElevatedButton("Создать аккаунт", width=300,height=50 , on_click=handle_auth, bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)
    google_btn = ft.ElevatedButton(
        content=ft.Row([
            ft.Image(src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg", width=20),
            ft.Text("Войти через Google", color=ft.Colors.BLACK, weight="bold"),
        ], alignment=ft.MainAxisAlignment.CENTER),
        width=300, height=50, bgcolor=ft.Colors.WHITE, on_click=auth_google 
    )
    toggle_btn = ft.TextButton("Уже есть аккаунт? Войти", on_click=toggle_mode)

    page.add(
        title_text,
        ft.Text("Платформа для особенных детей", color=ft.Colors.GREY_400),
        ft.Container(height=20),
        email_input,
        password_input,
        ft.Container(height=10),
        main_btn,
        google_btn,
        toggle_btn,
        status_text
    )

ft.app(target=main)