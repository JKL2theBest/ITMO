import pytest
import uuid
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_news_crud_flow(page: Page):
    """
    E2E сценарий:
    1. Логин (Admin).
    2. Создание новости.
    3. Проверка появления новости в списке.
    4. Переход на детальную страницу.
    5. Редактирование новости.
    6. Удаление новости.
    """

    # --- НАСТРОЙКИ ---
    FRONTEND_URL = "http://localhost:5173"
    EMAIL = "admin@example.com"
    PASSWORD = "admin_password"

    unique_id = str(uuid.uuid4())[:8]
    NEWS_TITLE = f"E2E Test News {unique_id}"
    NEWS_BODY = "This content is created by Playwright automated test."
    NEWS_TITLE_UPDATED = NEWS_TITLE + " (Updated)"

    # 1. ЛОГИН
    page.goto(f"{FRONTEND_URL}/login")

    page.fill('input[type="email"]', EMAIL)
    page.fill('input[type="password"]', PASSWORD)
    page.click('button[type="submit"]')

    # ОТЛАДКА:
    try:
        error_locator = page.locator("div[class*='error']")
        if error_locator.is_visible(timeout=2000):
            error_text = error_locator.text_content()
            raise AssertionError(
                f"Login failed on frontend with message: '{error_text}'"
            )
    except AssertionError as e:
        raise e
    except Exception:
        # Если элемента ошибки нет - идем дальше
        pass

    expect(page).to_have_url(f"{FRONTEND_URL}/", timeout=10000)

    create_btn = page.get_by_role("link", name="+ Создать")
    expect(create_btn).to_be_visible(timeout=5000)

    # 2. СОЗДАНИЕ НОВОСТИ
    create_btn.click()
    expect(page).to_have_url(f"{FRONTEND_URL}/create")

    page.fill('input[placeholder="Введите заголовок новости"]', NEWS_TITLE)
    page.fill('textarea[placeholder="Напишите текст новости здесь..."]', NEWS_BODY)
    page.click('button:has-text("Опубликовать")')

    expect(page).to_have_url(f"{FRONTEND_URL}/")

    # 3. ЧТЕНИЕ
    news_link = page.get_by_role("link", name=NEWS_TITLE).first
    expect(news_link).to_be_visible()

    # 4. ДЕТАЛЬНАЯ СТРАНИЦА
    news_link.click()

    expect(page.get_by_role("heading", name=NEWS_TITLE)).to_be_visible()
    expect(page.get_by_text(NEWS_BODY)).to_be_visible()

    # 5. РЕДАКТИРОВАНИЕ
    page.click('button:has-text("Редактировать")')

    page.fill('input[value*="E2E"]', NEWS_TITLE_UPDATED)
    page.click('button:has-text("Сохранить")')

    expect(page.get_by_role("heading", name=NEWS_TITLE_UPDATED)).to_be_visible()

    # 6. УДАЛЕНИЕ
    page.on("dialog", lambda dialog: dialog.accept())
    page.click('button:has-text("Удалить")')

    expect(page).to_have_url(f"{FRONTEND_URL}/")

    expect(page.get_by_role("link", name=NEWS_TITLE_UPDATED)).not_to_be_visible()
