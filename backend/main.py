"""
EmSana — кроссплатформенное приложение для детей с аутизмом (РАС).
Модуль: Карточки Домана — «Мир вещей: Животные».
Фреймворк: Flet 0.28.3+
"""

import flet as ft
import os


# ═══════════════════════════════════════════════════════════
#  Константы и настройки
# ═══════════════════════════════════════════════════════════

# Расширения файлов, которые мы считаем картинками / аудио
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
AUDIO_EXT = {".mp3", ".wav", ".ogg", ".m4a"}

# Директория ассетов (относительно корня проекта)
ASSETS_DIR = "assets"

# Путь к папке «Животные» (внимание: в реальной ФС есть пробел в конце!)
ANIMALS_PATH = os.path.join(ASSETS_DIR, "world_of_things", "Животные ")


# ═══════════════════════════════════════════════════════════
#  Цветовая палитра — спокойные тона для детей с РАС
# ═══════════════════════════════════════════════════════════

class C:
    """Цвета приложения."""
    # Главный экран (космос)
    SPACE_BG    = "#0B0C10"
    CARD_BG     = "#1F2833"
    ACCENT      = "#66FCF1"
    ACCENT_DIM  = "#45A29E"

    # Экран карточек
    LIGHT_BG    = "#F0F4F8"
    CARD_WHITE  = "#FFFFFF"
    TEXT_DARK   = "#1B2A4A"
    TEXT_MUTED  = "#8899AA"
    NAV_ICON    = "#3A506B"
    PLAY_BTN    = "#5B9BD5"
    DISABLED    = "#CBD5E0"


# ═══════════════════════════════════════════════════════════
#  Сканер папки с карточками
# ═══════════════════════════════════════════════════════════

def scan_cards(base_folder: str) -> list[dict]:
    """
    Сканирует двухуровневую структуру папок:
        base_folder / Категория / Элемент / {файлы}

    В каждой папке-элементе ищет первое изображение и первый
    аудиофайл. Если оба найдены — добавляет карточку в список.

    Возвращает список словарей:
        [{"name": "Медведь", "image": "relative/path.jpg",
          "audio": "relative/path.mp3"}, ...]
    """
    cards: list[dict] = []

    if not os.path.isdir(base_folder):
        print(f"⚠ Папка не найдена: {base_folder}")
        return cards

    # Перебираем категории (Домашние, Лесные, Экзотические …)
    try:
        categories = sorted(os.listdir(base_folder))
    except OSError:
        return cards

    for category in categories:
        cat_path = os.path.join(base_folder, category)
        if not os.path.isdir(cat_path):
            continue

        # Перебираем элементы (Медведь, Кошка, Змея …)
        try:
            items = sorted(os.listdir(cat_path))
        except OSError:
            continue

        for item_name in items:
            item_path = os.path.join(cat_path, item_name)
            if not os.path.isdir(item_path):
                continue

            image_file: str | None = None
            audio_file: str | None = None

            try:
                for filename in os.listdir(item_path):
                    ext = os.path.splitext(filename)[1].lower()
                    full = os.path.join(item_path, filename)

                    if not os.path.isfile(full):
                        continue

                    # Берём первую подходящую картинку / аудио
                    if ext in IMAGE_EXT and image_file is None:
                        image_file = os.path.relpath(full, ASSETS_DIR)
                    elif ext in AUDIO_EXT and audio_file is None:
                        audio_file = os.path.relpath(full, ASSETS_DIR)
            except OSError:
                continue

            # Добавляем карточку только если есть и картинка, и звук
            if image_file and audio_file:
                cards.append({
                    "name": item_name,
                    "image": image_file,
                    "audio": audio_file,
                })

    print(f"✓ Найдено карточек: {len(cards)}")
    return cards


# ═══════════════════════════════════════════════════════════
#  Главная функция приложения
# ═══════════════════════════════════════════════════════════

def main(page: ft.Page):
    # ── Базовые настройки страницы ──
    page.title = "EmSana"
    page.padding = 0
    page.bgcolor = C.SPACE_BG

    # Размер окна для десктоп-тестирования (на мобиле игнорируется)
    page.window.width = 420
    page.window.height = 780

    # ── Загрузка данных ──
    cards_data: list[dict] = scan_cards(ANIMALS_PATH)
    current_idx = {"v": 0}  # мутабельный контейнер для индекса

    # ── Аудиоплеер (живёт в overlay, работает на всех экранах) ──
    audio_player = ft.Audio(src="", autoplay=False)
    page.overlay.append(audio_player)

    def play_audio(src_path: str):
        """Воспроизводит аудиофайл по пути относительно assets."""
        try:
            audio_player.src = src_path
            audio_player.update()
            audio_player.play()
        except Exception as ex:
            print(f"⚠ Ошибка воспроизведения: {ex}")

    # ──────────────────────────────────────────────────────
    #  КАРТОЧКИ — мутабельные контролы (обновляются на месте)
    # ──────────────────────────────────────────────────────

    card_image_ctrl = ft.Image(
        src="",
        width=260,
        height=260,
        fit=ft.ImageFit.CONTAIN,
        border_radius=16,
    )

    card_name_ctrl = ft.Text(
        "",
        size=28,
        weight=ft.FontWeight.BOLD,
        color=C.TEXT_DARK,
        text_align=ft.TextAlign.CENTER,
    )

    counter_ctrl = ft.Text(
        "",
        size=14,
        color=C.TEXT_MUTED,
        weight=ft.FontWeight.W_500,
    )

    def on_prev(e):
        """Переход к предыдущей карточке."""
        if current_idx["v"] > 0:
            current_idx["v"] -= 1
            refresh_card()
            page.update()

    def on_next(e):
        """Переход к следующей карточке."""
        if current_idx["v"] < len(cards_data) - 1:
            current_idx["v"] += 1
            refresh_card()
            page.update()

    def on_play_sound(e):
        """Воспроизведение звука текущей карточки."""
        if cards_data:
            play_audio(cards_data[current_idx["v"]]["audio"])

    prev_btn_ctrl = ft.IconButton(
        icon=ft.Icons.ARROW_BACK_IOS_ROUNDED,
        icon_color=C.NAV_ICON,
        icon_size=28,
        on_click=on_prev,
    )

    next_btn_ctrl = ft.IconButton(
        icon=ft.Icons.ARROW_FORWARD_IOS_ROUNDED,
        icon_color=C.NAV_ICON,
        icon_size=28,
        on_click=on_next,
    )

    def refresh_card():
        """Обновляет значения контролов карточки по текущему индексу."""
        if not cards_data:
            return
        idx = max(0, min(current_idx["v"], len(cards_data) - 1))
        current_idx["v"] = idx
        card = cards_data[idx]
        total = len(cards_data)

        card_image_ctrl.src = card["image"]
        card_name_ctrl.value = card["name"]
        counter_ctrl.value = f"{idx + 1} / {total}"

        is_first = idx == 0
        is_last = idx == total - 1

        prev_btn_ctrl.disabled = is_first
        prev_btn_ctrl.icon_color = C.NAV_ICON if not is_first else C.DISABLED
        next_btn_ctrl.disabled = is_last
        next_btn_ctrl.icon_color = C.NAV_ICON if not is_last else C.DISABLED

    # ══════════════════════════════════════════════════════
    #   ГЛАВНЫЙ ЭКРАН — тема «Космос»
    # ══════════════════════════════════════════════════════

    def build_home() -> ft.View:
        """Строит главный экран с космической тематикой."""

        def go_to_cards(e):
            current_idx["v"] = 0
            page.go("/cards")

        # Звёзды-декорации (x, y, размер, прозрачность)
        star_data = [
            (25,  100, 15, 0.25), (340,  65,  9, 0.18),
            (55,  280, 11, 0.30), (310, 220, 17, 0.15),
            (175,  50,  7, 0.20), (260, 380, 13, 0.28),
            (35,  480, 10, 0.22), (330, 530,  8, 0.16),
            (145, 430, 12, 0.26), (90,  170,  6, 0.19),
            (285, 140, 14, 0.24), (210, 320,  9, 0.17),
            (120, 600,  8, 0.21), (370, 420, 11, 0.14),
        ]
        stars = [
            ft.Container(
                content=ft.Icon(
                    ft.Icons.STAR_ROUNDED,
                    color=C.ACCENT,
                    size=size,
                    opacity=opacity,
                ),
                left=x, top=y,
            )
            for x, y, size, opacity in star_data
        ]

        # Центральная карточка-кнопка
        theme_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            # Аватарка пользователя
                            ft.CircleAvatar(
                                content=ft.Icon(
                                    ft.Icons.CHILD_CARE_ROUNDED,
                                    color=ft.Colors.WHITE,
                                    size=28,
                                ),
                                bgcolor="#2A3A4A",
                                radius=30,
                            ),
                            ft.Container(width=20),
                            # Иконка ракеты и надпись «Космос»
                            ft.Column(
                                controls=[
                                    ft.Icon(
                                        ft.Icons.ROCKET_LAUNCH_ROUNDED,
                                        color=C.ACCENT,
                                        size=48,
                                    ),
                                    ft.Text(
                                        "Космос",
                                        color=ft.Colors.WHITE,
                                        size=17,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=4,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=300,
            height=150,
            bgcolor=C.CARD_BG,
            border_radius=25,
            padding=24,
            shadow=ft.BoxShadow(
                blur_radius=25,
                color=C.ACCENT_DIM,
                offset=ft.Offset(0, 4),
            ),
            on_click=go_to_cards,
            ink=True,
            ink_color="#45A29E33",
        )

        # Кнопка «Я родитель» (сверху слева)
        parent_button = ft.TextButton(
            text="Я родитель",
            icon=ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED,
            icon_color=C.ACCENT_DIM,
            style=ft.ButtonStyle(color=C.ACCENT),
        )

        # Заголовок приложения
        title_col = ft.Column(
            controls=[
                ft.Text(
                    "EmSana",
                    size=34,
                    weight=ft.FontWeight.BOLD,
                    color=C.ACCENT,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Мир знаний для вашего ребёнка",
                    size=14,
                    color=C.ACCENT_DIM,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        )

        return ft.View(
            route="/",
            bgcolor=C.SPACE_BG,
            padding=0,
            controls=[
                ft.Stack(
                    controls=[
                        # Звёзды на фоне
                        *stars,
                        # Основной контент поверх звёзд
                        ft.Column(
                            controls=[
                                ft.Container(
                                    content=parent_button,
                                    padding=ft.Padding(8, 50, 0, 0),
                                ),
                                ft.Container(expand=True),
                                title_col,
                                ft.Container(height=30),
                                ft.Row(
                                    controls=[theme_card],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                ft.Container(expand=True),
                            ],
                            expand=True,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    expand=True,
                ),
            ],
        )

    # ══════════════════════════════════════════════════════
    #   ЭКРАН КАРТОЧЕК ДОМАНА
    # ══════════════════════════════════════════════════════

    def build_cards() -> ft.View:
        """Строит экран просмотра карточек Домана."""

        # Кнопка «Назад» на главную
        back_btn = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            icon_color=C.NAV_ICON,
            icon_size=28,
            on_click=lambda e: page.go("/"),
        )

        # --- Если нет карточек — показываем заглушку ---
        if not cards_data:
            return ft.View(
                route="/cards",
                bgcolor=C.LIGHT_BG,
                padding=20,
                controls=[
                    ft.Row(controls=[back_btn]),
                    ft.Container(expand=True),
                    ft.Column(
                        controls=[
                            ft.Icon(
                                ft.Icons.SENTIMENT_DISSATISFIED_ROUNDED,
                                size=64,
                                color=C.TEXT_MUTED,
                            ),
                            ft.Container(height=12),
                            ft.Text(
                                "Карточки не найдены",
                                size=20,
                                color=C.TEXT_DARK,
                                weight=ft.FontWeight.W_600,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                "Проверьте папку assets/world_of_things",
                                size=14,
                                color=C.TEXT_MUTED,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                    ),
                    ft.Container(expand=True),
                ],
            )

        # --- Есть карточки — строим полноценный экран ---

        # Устанавливаем данные контролов (без page.update — view ещё не на экране)
        refresh_card()

        # Карточка с изображением (клик воспроизводит звук)
        image_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=card_image_ctrl,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(height=12),
                    card_name_ctrl,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=C.CARD_WHITE,
            border_radius=24,
            padding=ft.Padding(24, 28, 24, 24),
            shadow=ft.BoxShadow(
                blur_radius=20,
                color="#0000000D",
                offset=ft.Offset(0, 8),
            ),
            width=340,
            on_click=on_play_sound,
            ink=True,
            ink_color="#5B9BD520",
        )

        # Кнопка воспроизведения (между стрелками)
        play_btn = ft.Container(
            content=ft.Icon(
                ft.Icons.VOLUME_UP_ROUNDED,
                color=ft.Colors.WHITE,
                size=30,
            ),
            width=60,
            height=60,
            bgcolor=C.PLAY_BTN,
            border_radius=20,
            alignment=ft.alignment.center,
            on_click=on_play_sound,
            shadow=ft.BoxShadow(
                blur_radius=12,
                color="#5B9BD540",
                offset=ft.Offset(0, 4),
            ),
        )

        # Навигация: ← 🔊 →
        nav_row = ft.Row(
            controls=[prev_btn_ctrl, play_btn, next_btn_ctrl],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=28,
        )

        # Верхняя панель: ← Животные        1/24
        top_bar = ft.Row(
            controls=[
                back_btn,
                ft.Text(
                    "Животные",
                    size=20,
                    weight=ft.FontWeight.W_600,
                    color=C.TEXT_DARK,
                ),
                ft.Container(expand=True),
                ft.Container(
                    content=counter_ctrl,
                    bgcolor="#E8EDF2",
                    border_radius=12,
                    padding=ft.Padding(12, 6, 12, 6),
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.View(
            route="/cards",
            bgcolor=C.LIGHT_BG,
            padding=ft.Padding(16, 50, 16, 24),
            controls=[
                top_bar,
                ft.Container(expand=True),
                ft.Row(
                    controls=[image_card],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(height=24),
                nav_row,
                ft.Container(expand=True),
            ],
        )

    # ══════════════════════════════════════════════════════
    #   РОУТИНГ
    # ══════════════════════════════════════════════════════

    def on_route_change(e: ft.RouteChangeEvent):
        """Обработчик смены маршрута — переключает экраны."""
        page.views.clear()

        if page.route == "/cards":
            page.views.append(build_cards())
        else:
            page.views.append(build_home())

        page.update()

    def on_view_pop(e: ft.ViewPopEvent):
        """Обработчик кнопки «Назад» системы / браузера."""
        page.views.pop()
        top = page.views[-1] if page.views else None
        page.go(top.route if top else "/")

    page.on_route_change = on_route_change
    page.on_view_pop = on_view_pop

    # Первый переход — на главный экран
    page.go("/")


# ── Запуск ──
ft.app(target=main, assets_dir="assets")