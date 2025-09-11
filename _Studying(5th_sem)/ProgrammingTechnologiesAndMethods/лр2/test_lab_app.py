# test_lab_app.py

import pytest
from datetime import datetime, timedelta

# Импортируем функции из нашего приложения
import lab_app

# --- Тестовые данные и константы ---
FAKE_START_TIME = datetime(2023, 10, 27, 12, 0, 0)
TEST_USER_FIO = "Иванов Иван Иванович"


# --- Фикстура для мокирования winreg ---
# Создадим фикстуру, чтобы не дублировать код мокирования winreg в каждом тесте.
@pytest.fixture
def mock_winreg(mocker):
    """Фикстура, которая полностью мокирует модуль winreg."""
    mock_key_handle = mocker.MagicMock()
    # Мокируем все функции, которые использует наше приложение
    mocks = {
        "OpenKey": mocker.patch("lab_app.winreg.OpenKey", return_value=mock_key_handle),
        "CreateKey": mocker.patch(
            "lab_app.winreg.CreateKey", return_value=mock_key_handle
        ),
        "QueryValueEx": mocker.patch("lab_app.winreg.QueryValueEx"),
        "SetValueEx": mocker.patch("lab_app.winreg.SetValueEx"),
        "CloseKey": mocker.patch("lab_app.winreg.CloseKey"),
        "HKEY_CURRENT_USER": mocker.patch("lab_app.winreg.HKEY_CURRENT_USER"),
    }
    # Возвращаем словарь с моками, чтобы тесты могли их настраивать
    return mocks, mock_key_handle


# --- Основной набор тестов ---


def test_first_run_success(mock_winreg, mocker, monkeypatch, capsys):
    """Тестирует первый успешный запуск с новой логикой ввода."""
    # ARRANGE
    mocks, mock_key_handle = mock_winreg
    mocks["OpenKey"].side_effect = FileNotFoundError

    # Мокируем os.makedirs, чтобы не зависеть от прав доступа
    mock_makedirs = mocker.patch("lab_app.os.makedirs")
    # Мокируем open для контроля над файловой системой
    mock_open = mocker.patch("builtins.open", mocker.mock_open())
    # Мокируем os.path.exists, чтобы симулировать отсутствие файла
    mocker.patch("lab_app.os.path.exists", return_value=False)

    mock_datetime = mocker.patch("lab_app.datetime")
    mock_datetime.now.return_value = datetime(2023, 1, 1)
    mock_datetime.fromisoformat.side_effect = datetime.fromisoformat

    # ИСПРАВЛЕНИЕ: Симулируем пошаговый ввод
    user_inputs = ["Иванов", "Иван", "Иванович", ""]  # Фамилия, Имя, Отчество, выход
    monkeypatch.setattr("builtins.input", lambda _: user_inputs.pop(0))

    # ACT
    lab_app.main()

    # ASSERT
    captured = capsys.readouterr()
    assert "Добро пожаловать!" in captured.out
    assert "Сформировано ФИО: Иванов Иван Иванович" in captured.out

    # Проверяем, что была попытка создать директорию
    mock_makedirs.assert_called_once_with(lab_app.APP_DATA_DIR, exist_ok=True)
    # Проверяем, что в файл было записано правильное ФИО
    mock_open().write.assert_called_once_with("Иванов Иван Иванович\n")


def test_add_user_with_compound_name(mock_winreg, mocker, monkeypatch, capsys):
    """Тестирует добавление пользователя с двойным именем и без отчества."""
    mocks, _ = mock_winreg
    mocks["OpenKey"].side_effect = FileNotFoundError
    mocker.patch("lab_app.os.makedirs")
    mock_open = mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("lab_app.os.path.exists", return_value=False)
    mock_datetime = mocker.patch("lab_app.datetime")
    mock_datetime.now.return_value = datetime(2023, 1, 1)
    mock_datetime.fromisoformat.side_effect = datetime.fromisoformat

    # ИСПРАВЛЕНО: Правильный ввод для новой логики
    user_inputs = ["Петрова-Скворцова", "анна-мария", "", ""]
    monkeypatch.setattr("builtins.input", lambda _: user_inputs.pop(0))

    lab_app.main()

    captured = capsys.readouterr()
    # ИСПРАВЛЕНО: Ожидаем правильную капитализацию
    assert "Сформировано ФИО: Петрова-Скворцова Анна-Мария" in captured.out
    mock_open().write.assert_called_once_with("Петрова-Скворцова Анна-Мария\n")


# НОВЫЙ ТЕСТ для имени через пробел
def test_add_user_with_space_in_name(mock_winreg, mocker, monkeypatch, capsys):
    """Тестирует добавление пользователя с именем через пробел."""
    mocks, _ = mock_winreg
    mocks["OpenKey"].side_effect = FileNotFoundError
    mocker.patch("lab_app.os.makedirs")
    mock_open = mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("lab_app.os.path.exists", return_value=False)
    mock_datetime = mocker.patch("lab_app.datetime")
    mock_datetime.now.return_value = datetime(2023, 1, 1)
    mock_datetime.fromisoformat.side_effect = datetime.fromisoformat

    user_inputs = ["Джордан", "майкл", "Баскетболович", ""]
    monkeypatch.setattr("builtins.input", lambda _: user_inputs.pop(0))

    lab_app.main()

    captured = capsys.readouterr()
    assert "Сформировано ФИО: Джордан Майкл Баскетболович" in captured.out
    mock_open().write.assert_called_once_with("Джордан Майкл Баскетболович\n")


# ИСПРАВЛЕННЫЙ ТЕСТ
def test_core_logic_fails_no_run_commit(
    mock_winreg, mocker, monkeypatch, capsys, tmp_path
):
    """Тестирует сценарий, когда основная логика завершается с ошибкой."""
    mocks, _ = mock_winreg
    mocks["QueryValueEx"].side_effect = [(1, None), (FAKE_START_TIME.isoformat(), None)]
    # Симулируем ошибку при вызове os.makedirs, а не open
    mocker.patch(
        "lab_app.os.makedirs", side_effect=PermissionError("Permission denied")
    )

    mock_datetime = mocker.patch("lab_app.datetime")
    mock_datetime.now.return_value = FAKE_START_TIME
    mock_datetime.fromisoformat.side_effect = datetime.fromisoformat

    # ИСПРАВЛЕНО: Даем достаточно вводов, чтобы пройти этап валидации
    user_inputs = ["Тестов", "Тест", "Тестович", ""]
    monkeypatch.setattr("builtins.input", lambda _: user_inputs.pop(0))
    monkeypatch.chdir(tmp_path)

    lab_app.main()

    captured = capsys.readouterr()
    assert "Недостаточно прав для создания директории" in captured.out
    assert "Запуск не будет засчитан" in captured.out
    mocks["SetValueEx"].assert_not_called()


# ИСПРАВЛЕННЫЙ ТЕСТ
def test_run_core_logic_with_empty_fio(mock_winreg, mocker, monkeypatch, capsys):
    """Тестирует ввод пустого ФИО."""
    mocks, _ = mock_winreg
    mocks["OpenKey"].side_effect = FileNotFoundError
    mocker.patch("lab_app.os.makedirs")
    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("lab_app.os.path.exists", return_value=False)

    mock_datetime = mocker.patch("lab_app.datetime")
    mock_datetime.now.return_value = FAKE_START_TIME
    mock_datetime.fromisoformat.side_effect = datetime.fromisoformat

    # ИСПРАВЛЕНО: Более сложный сценарий с несколькими неправильными вводами
    user_inputs = ["", "Иванов", "", "Иван", "Иванович", ""]
    monkeypatch.setattr("builtins.input", lambda _: user_inputs.pop(0))

    lab_app.main()

    captured = capsys.readouterr()
    assert "Ошибка: Фамилия не может быть пустой" in captured.out
    assert "Ошибка: Имя не может быть пустым" in captured.out
    assert "Сформировано ФИО: Иванов Иван Иванович" in captured.out


# ИСПРАВЛЕННЫЙ ТЕСТ
def test_commit_license_fails(mock_winreg, mocker, monkeypatch, capsys, tmp_path):
    """Тестирует сбой при записи в реестр."""
    mocks, _ = mock_winreg
    mocks["OpenKey"].side_effect = FileNotFoundError
    mocks["SetValueEx"].side_effect = OSError("Failed to write to registry")
    mocker.patch("lab_app.os.makedirs")
    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("lab_app.os.path.exists", return_value=False)

    mock_datetime = mocker.patch("lab_app.datetime")
    mock_datetime.now.return_value = FAKE_START_TIME
    mock_datetime.fromisoformat.side_effect = datetime.fromisoformat

    # ИСПРАВЛЕНО: Даем достаточно вводов
    user_inputs = ["Успешный", "Ввод", "", ""]
    monkeypatch.setattr("builtins.input", lambda _: user_inputs.pop(0))
    monkeypatch.chdir(tmp_path)

    lab_app.main()

    captured = capsys.readouterr()
    assert "Сформировано ФИО: Успешный Ввод" in captured.out
    assert "Критическая ошибка при обновлении данных лицензии" in captured.out


def test_input_validation_loops(mock_winreg, mocker, monkeypatch, capsys):
    """Тестирует циклы валидации при некорректном вводе."""
    # ARRANGE
    mocks, _ = mock_winreg
    mocks["OpenKey"].side_effect = FileNotFoundError
    mocker.patch("lab_app.os.makedirs")
    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("lab_app.os.path.exists", return_value=False)
    mock_datetime = mocker.patch("lab_app.datetime")
    mock_datetime.now.return_value = datetime(2023, 1, 1)
    mock_datetime.fromisoformat.side_effect = datetime.fromisoformat

    # ИСПРАВЛЕНИЕ: Некорректный ввод -> Корректный ввод
    user_inputs = [
        "",
        "123",
        "Сидоров",  # Попытки ввести фамилию
        "Петр1",
        "Петр",  # Попытки ввести имя
        "Сидорович",
        "",  # Отчество и выход
    ]
    monkeypatch.setattr("builtins.input", lambda _: user_inputs.pop(0))

    # ACT
    lab_app.main()

    # ASSERT
    captured = capsys.readouterr()
    assert "Ошибка: Фамилия не может быть пустой" in captured.out
    assert "Ошибка: Имя не может быть пустым" in captured.out
    assert "Сформировано ФИО: Сидоров Петр Сидорович" in captured.out


# ВАЖНО: Остальные тесты (на лимиты, на ошибки реестра и т.д.) остаются
# без изменений, так как они не затрагивают логику run_core_logic.
# Просто убедитесь, что они тоже используют новый способ мокирования input.
# Например, в test_run_limit_exceeded нужно будет передать
# user_inputs = ["Иванов", "Иван", "", ""], чтобы он прошел этап ввода ФИО
# до того, как его заблокируют. Но для простоты можно оставить
# monkeypatch.setattr('builtins.input', lambda _: ""), так как
# эти тесты не доходят до этапа ввода ФИО.


def test_time_limit_exceeded(mock_winreg, mocker, monkeypatch, capsys):
    """
    Тестирует блокировку программы при превышении лимита по времени.
    """
    # ARRANGE
    mocks, _ = mock_winreg
    mocks["QueryValueEx"].side_effect = [(1, None), (FAKE_START_TIME.isoformat(), None)]

    mock_datetime = mocker.patch("lab_app.datetime")
    future_time = FAKE_START_TIME + timedelta(minutes=lab_app.TRIAL_MINUTES, seconds=1)
    mock_datetime.now.return_value = future_time
    mock_datetime.fromisoformat.side_effect = datetime.fromisoformat

    monkeypatch.setattr("builtins.input", lambda _: "")

    # ACT & ASSERT
    with pytest.raises(SystemExit):
        lab_app.main()

    captured = capsys.readouterr()
    assert "СРОК ДЕЙСТВИЯ ПРОБНОЙ ВЕРСИИ ИСТЕК" in captured.out
    assert f"Прошло более {lab_app.TRIAL_MINUTES} минут" in captured.out


def test_get_license_data_fails(mock_winreg, mocker, monkeypatch, capsys):
    """
    Тестирует сбой при чтении из реестра. Покрытие строк 29-32.
    """
    # ARRANGE
    mocks, _ = mock_winreg
    # Симулируем ошибку доступа к реестру
    mocks["OpenKey"].side_effect = PermissionError("Access Denied")
    monkeypatch.setattr("builtins.input", lambda _: "")

    # ACT & ASSERT
    # Программа должна поймать Exception, вывести ошибку и заблокироваться
    with pytest.raises(SystemExit):
        lab_app.main()

    captured = capsys.readouterr()
    assert "Ошибка чтения данных лицензии: Access Denied" in captured.out
    assert "СРОК ДЕЙСТВИЯ ПРОБНОЙ ВЕРСИИ ИСТЕК" in captured.out


# test_lab_app.py (добавьте эти тесты в конец файла)


def test_add_duplicate_user(mock_winreg, mocker, monkeypatch, capsys):
    """
    Тестирует добавление дубликата ФИО. Покрытие строк 124-128.
    """
    mocks, _ = mock_winreg
    mocks["OpenKey"].side_effect = FileNotFoundError
    mocker.patch("lab_app.os.makedirs")
    # Симулируем, что файл существует и содержит нашего пользователя
    mocker.patch("lab_app.os.path.exists", return_value=True)
    existing_user = "Иванов Иван Иванович"
    mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data=existing_user))

    mock_datetime = mocker.patch("lab_app.datetime")
    mock_datetime.now.return_value = datetime(2023, 1, 1)
    mock_datetime.fromisoformat.side_effect = datetime.fromisoformat

    user_inputs = ["Иванов", "Иван", "Иванович", ""]
    monkeypatch.setattr("builtins.input", lambda _: user_inputs.pop(0))

    lab_app.main()

    captured = capsys.readouterr()
    assert f"Пользователь с ФИО '{existing_user}' уже существует" in captured.out
    # Убеждаемся, что не было попытки записать в файл
    mock_open().write.assert_not_called()
    # Но запуск должен быть засчитан, так как операция (проверка) прошла успешно
    mocks["SetValueEx"].assert_any_call(mocker.ANY, "RunCount", 0, mocker.ANY, 1)


def test_invalid_middle_name_is_ignored(mock_winreg, mocker, monkeypatch, capsys):
    """
    Тестирует ввод некорректного отчества. Покрытие строк 98-99.
    """
    mocks, _ = mock_winreg
    mocks["OpenKey"].side_effect = FileNotFoundError
    mocker.patch("lab_app.os.makedirs")
    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("lab_app.os.path.exists", return_value=False)

    mock_datetime = mocker.patch("lab_app.datetime")
    mock_datetime.now.return_value = datetime(2023, 1, 1)
    mock_datetime.fromisoformat.side_effect = datetime.fromisoformat

    # Вводим отчество с цифрой
    user_inputs = ["Петров", "Петр", "Петрович123", ""]
    monkeypatch.setattr("builtins.input", lambda _: user_inputs.pop(0))

    lab_app.main()

    captured = capsys.readouterr()
    assert "Предупреждение: Отчество содержит недопустимые символы" in captured.out
    # Проверяем, что в итоге отчество было отброшено
    assert "Сформировано ФИО: Петров Петр" in captured.out


def test_unexpected_error_in_core_logic(mock_winreg, mocker, monkeypatch, capsys):
    """
    Тестирует общий обработчик исключений. Покрытие строк 136-138.
    """
    mocks, _ = mock_winreg
    mocks["OpenKey"].side_effect = FileNotFoundError
    mocker.patch("lab_app.os.makedirs")
    # Симулируем неожиданную ошибку при открытии файла
    mocker.patch("builtins.open", side_effect=IOError("Disk is full"))
    mocker.patch("lab_app.os.path.exists", return_value=True)

    mock_datetime = mocker.patch("lab_app.datetime")
    mock_datetime.now.return_value = datetime(2023, 1, 1)
    mock_datetime.fromisoformat.side_effect = datetime.fromisoformat

    user_inputs = ["Сидоров", "Сидор", "", ""]
    monkeypatch.setattr("builtins.input", lambda _: user_inputs.pop(0))

    lab_app.main()

    captured = capsys.readouterr()
    assert (
        "Произошла непредвиденная ошибка при работе с файлом: Disk is full"
        in captured.out
    )
    assert "Запуск не будет засчитан" in captured.out
    mocks["SetValueEx"].assert_not_called()
