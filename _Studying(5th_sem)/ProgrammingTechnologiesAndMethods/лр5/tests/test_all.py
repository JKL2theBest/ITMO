# -*- coding: utf-8 -*-
"""Единый набор тестов для всего проекта."""
import sys
from unittest.mock import patch
import pytest
import random

# Импорты должны быть наверху. Ruff был прав.
from ciphers import scytale, cardan_grille
from ciphers.base_cipher import BaseCipher
from main import main
from ui import console_ui


# --- 1. Тесты бизнес-логики (ciphers) ---

def test_scytale_cycle():
    """Тест полного цикла для Скиталы."""
    text = "Это тестовый текст для проверки"
    key = 5
    encrypted = scytale.encrypt(text, key)
    assert scytale.decrypt(encrypted, key) == text

def test_cardan_cycle():
    """Тест полного цикла для Решётки Кардано."""
    random.seed(42)  # Для предсказуемости
    grille = cardan_grille.generate_grille(6)
    text = "Это тестовый текст для решетки!!".ljust(36)
    encrypted = cardan_grille.encrypt(text, grille)
    assert cardan_grille.decrypt(encrypted, grille) == text

# --- 2. Тесты обвязки (main, base_cipher) ---

@patch('ui.gui_ui.start_ui')
def test_main_starts_gui_by_default(mock_start, monkeypatch):
    """Тест: main.py запускает GUI по умолчанию."""
    monkeypatch.setattr(sys, 'argv', ['main.py'])
    main()
    mock_start.assert_called_once()


@patch('ui.console_ui.start_ui')
def test_main_starts_console_with_flag(mock_start, monkeypatch):
    """Тест: main.py запускает консоль с флагом --console."""
    monkeypatch.setattr(sys, 'argv', ['main.py', '--console'])
    main()
    mock_start.assert_called_once()


def test_base_cipher_implementation():
    """Тест для покрытия и проверки контракта BaseCipher."""
    class GoodCipher(BaseCipher):
        def encrypt(self, text, key):
            return text
        def decrypt(self, text, key):
            return text

    GoodCipher().encrypt("a", 1)

    with pytest.raises(TypeError):
        class BadCipher(BaseCipher):
            def encrypt(self, text, key):
                return text
        BadCipher()

# --- 3. Тесты КОНСОЛЬНОГО UI ---

CONSOLE_SCENARIOS = [
    # Успешный сценарий
    (['1', '1', '1', 'текст', '3', '1', '', '3'], "Операция выполнена"),
    # Неверный выбор в меню
    (['invalid', '', '3'], "Неверный выбор"),
    # Выход по команде
    (['выход'], "Завершение работы"),
]
@pytest.mark.parametrize("inputs, output", CONSOLE_SCENARIOS)
def test_console_sessions(monkeypatch, capsys, inputs, output):
    """Тест основных сценариев консольного UI."""
    # Каждый раз создаем новый итератор.
    monkeypatch.setattr('builtins.input', lambda _: iter(inputs).__next__())
    console_ui.start_ui()
    assert output in capsys.readouterr().out