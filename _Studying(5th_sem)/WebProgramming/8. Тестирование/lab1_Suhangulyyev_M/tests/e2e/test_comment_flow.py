import pytest
import uuid
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_user_registration_and_comments_flow(page: Page):
    """
    E2E сценарий "Жизненный цикл комментария":
    1. Админ заходит и создает новость.
    2. Админ выходит.
    3. Новый пользователь регистрируется.
    4. Пользователь находит новость Админа.
    5. Оставляет комментарий.
    6. Редактирует его.
    7. Удаляет его.
    """

    # --- НАСТРОЙКИ ---
    FRONTEND_URL = "http://localhost:5173"

    ADMIN_EMAIL = "admin@example.com"
    ADMIN_PASS = "admin_password"

    unique_id = str(uuid.uuid4())[:8]
    NEW_USER_NAME = f"Commenter_{unique_id}"
    NEW_USER_EMAIL = f"new_{unique_id}@test.com"
    NEW_USER_PASS = "password123"

    NEWS_TITLE = f"News for Comments {unique_id}"
    NEWS_BODY = "Content to be commented on."
    COMMENT_TEXT = f"My first comment {unique_id}"
    COMMENT_TEXT_UPDATED = f"My edited comment {unique_id}"

    # 1. Админ создает новость
    page.goto(f"{FRONTEND_URL}/login")
    page.fill('input[type="email"]', ADMIN_EMAIL)
    page.fill('input[type="password"]', ADMIN_PASS)
    page.click('button[type="submit"]')

    expect(page).to_have_url(f"{FRONTEND_URL}/")

    page.get_by_role("link", name="+ Создать").click()
    page.fill('input[placeholder="Введите заголовок новости"]', NEWS_TITLE)
    page.fill('textarea[placeholder="Напишите текст новости здесь..."]', NEWS_BODY)
    page.click('button:has-text("Опубликовать")')

    expect(page.get_by_text(NEWS_TITLE)).to_be_visible()

    page.click('button:has-text("Выйти")')
    expect(page).to_have_url(f"{FRONTEND_URL}/login")

    # 2. Регистрация нового пользователя
    page.click('text="Зарегистрироваться"')
    expect(page).to_have_url(f"{FRONTEND_URL}/register")

    page.fill('input[placeholder="Имя пользователя"]', NEW_USER_NAME)
    page.fill('input[placeholder="Email"]', NEW_USER_EMAIL)
    page.fill('input[placeholder="Пароль"]', NEW_USER_PASS)
    page.click('button:has-text("Зарегистрироваться")')

    expect(page).to_have_url(f"{FRONTEND_URL}/")

    expect(page.get_by_text(NEW_USER_NAME)).to_be_visible()

    # 3. Комментирование
    page.click(f"text={NEWS_TITLE}")

    page.fill('textarea[placeholder="Написать комментарий..."]', COMMENT_TEXT)
    page.click('button:has-text("Отправить")')

    expect(page.get_by_text(COMMENT_TEXT)).to_be_visible()
    expect(page.get_by_text(NEW_USER_NAME).first).to_be_visible()

    # 4. Редактирование комментария
    page.click('button:has-text("Изменить")')

    page.fill(f'textarea:has-text("{COMMENT_TEXT}")', COMMENT_TEXT_UPDATED)
    page.click('button:has-text("Сохранить")')

    expect(page.get_by_text(COMMENT_TEXT_UPDATED)).to_be_visible()
    expect(page.get_by_text(COMMENT_TEXT)).not_to_be_visible()

    # 5. Удаление комментария
    page.on("dialog", lambda dialog: dialog.accept())

    page.click('button:has-text("Удалить")')

    expect(page.get_by_text(COMMENT_TEXT_UPDATED)).not_to_be_visible()
