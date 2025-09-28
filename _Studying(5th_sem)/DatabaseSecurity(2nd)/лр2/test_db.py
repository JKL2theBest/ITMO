import pytest
import psycopg2

# --- Параметры подключения к БД ---
DB_PARAMS = {
    "host": "localhost",
    "port": 5252,
    "user": "postgres",
    "password": "пароль",
    "dbname": "scooter_rental_db",
}


@pytest.fixture(scope="module")
def db_connection():
    """Фикстура для создания и закрытия соединения с БД."""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        yield conn
        conn.close()
    except psycopg2.OperationalError as e:
        pytest.fail(f"Не удалось подключиться к базе данных: {e}")


def test_connection_is_successful(db_connection):
    """Проверяет, что соединение с БД успешно установлено."""
    assert db_connection is not None and not db_connection.closed


def test_users_table_is_populated(db_connection):
    """Проверяет, что таблица "User" содержит данные (не пустая)."""
    with db_connection.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM public."User"')
        user_count = cur.fetchone()[0]
        assert user_count >= 8, "В таблице User должно быть не менее 8 записей"


def test_scooters_for_charging_view_logic(db_connection):
    """Проверяет логику представления 'scooters_for_charging': все самокаты в нем должны иметь заряд < 30%."""
    with db_connection.cursor() as cur:
        cur.execute('SELECT "Текущий уровень заряда" FROM public.scooters_for_charging')
        low_charge_levels = cur.fetchall()
        for level in low_charge_levels:
            assert (
                level[0] < 30
            ), f"Найден самокат с уровнем заряда {level[0]}, что не соответствует логике представления"


def test_foreign_key_constraint(db_connection):
    """Проверяет работу ограничения внешнего ключа, пытаясь вставить поездку с несуществующим UserID."""
    with pytest.raises(psycopg2.errors.ForeignKeyViolation):
        with db_connection.cursor() as cur:
            invalid_user_id = 999999
            cur.execute(
                "INSERT INTO public.Trip (UserID, ScooterID, TariffID, StartTime) VALUES (%s, 1, 1, NOW())",
                (invalid_user_id,),
            )
    db_connection.rollback()


def test_unique_email_constraint(db_connection):
    """Проверяет работу ограничения UNIQUE для Email в таблице "User", пытаясь вставить дубликат."""
    with pytest.raises(psycopg2.errors.UniqueViolation):
        with db_connection.cursor() as cur:
            existing_email = "ivanov@email.com"
            cur.execute(
                'INSERT INTO public."User" (FIO, PhoneNumber, Email) VALUES (%s, %s, %s)',
                ("Тестовый Пользователь", "+70000000000", existing_email),
            )
    db_connection.rollback()


def test_scooter_status_default_value(db_connection):
    """Проверяет, что для нового самоката по умолчанию устанавливается статус 'available'."""
    with db_connection.cursor() as cur:
        cur.execute(
            "INSERT INTO public.Scooter (Model, ChargeLevel, ZoneID) VALUES (%s, %s, %s) RETURNING ScooterID",
            ("Test Model", 100, 1),
        )
        new_scooter_id = cur.fetchone()[0]

        cur.execute(
            "SELECT Status FROM public.Scooter WHERE ScooterID = %s", (new_scooter_id,)
        )
        status = cur.fetchone()[0]

        assert status == "available"

    db_connection.rollback()
