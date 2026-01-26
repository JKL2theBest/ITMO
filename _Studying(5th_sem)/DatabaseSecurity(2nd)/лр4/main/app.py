import datetime
import json
import os  # Для безопасного получения секретного ключа
from functools import wraps
from decimal import Decimal
import jwt
from flask import Flask, Response, request, render_template
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
from models import get_session

# --- Конфигурация Flask приложения ---
app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "my_super_secret_for_jwt_in_lab_4_default"
)
app.config["JSON_AS_ASCII"] = False

# --- "База данных" пользователей API ---
# ВАЖНО: В реальном приложении эта информация должна храниться в таблице БД.
# Для лабораторной работы это допустимое упрощение.
api_users = {
    "anna_client": {
        "password_hash": generate_password_hash("clientpass123"),
        "role": "client",
        "db_user": "anna_vasilieva_client",
        "db_pass": "clientpass123",
    },
    "sergey_tech": {
        "password_hash": generate_password_hash("techpass456"),
        "role": "technician",
        "db_user": "sergey_mikhailov_tech",
        "db_pass": "techpass456",
    },
}


# --- Вспомогательные функции и декораторы ---
def create_json_response(data, status_code=200):
    """Централизованно создает Flask Response с корректным заголовком и кодировкой UTF-8."""
    json_data = json.dumps(data, ensure_ascii=False, indent=2)
    return Response(
        json_data, mimetype="application/json; charset=utf-8", status=status_code
    )


def token_required(f):
    """Декоратор для защиты эндпоинтов, требующих JWT-аутентификации."""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers and request.headers[
            "Authorization"
        ].startswith("Bearer "):
            token = request.headers["Authorization"].split(" ")[1]

        if not token:
            return create_json_response(
                {"message": "Токен аутентификации отсутствует!"}, 401
            )

        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user = api_users.get(data["user"])
            if not current_user:
                return create_json_response(
                    {"message": "Пользователь из токена не найден!"}, 401
                )
        except jwt.ExpiredSignatureError:
            return create_json_response({"message": "Срок действия токена истек!"}, 401)
        except jwt.InvalidTokenError:
            return create_json_response({"message": "Токен недействителен!"}, 401)

        return f(current_user, *args, **kwargs)

    return decorated


# --- Маршруты для UI ---
@app.route("/ui/login")
def ui_login_page():
    return render_template("login.html")


@app.route("/ui/client")
def ui_client_dashboard_page():
    return render_template("client_dashboard.html")


@app.route("/ui/technician")
def ui_technician_dashboard_page():
    return render_template("technician_dashboard.html")


# --- Маршруты для API ---
@app.route("/")
def index_page():
    """Главная страница API, предоставляет информацию о доступных эндпоинтах."""
    data = {
        "message": "API для системы проката самокатов",
        "api_endpoints": {
            "POST /login": "Получение JWT токена (Basic Auth)",
            "GET /api/client/scooters": "Получить доступные самокаты (для клиентов)",
            "GET /api/tech/maintenance_log": "Получить журнал ТО (для техников)",
        },
        "ui_entry_point": {"login_page": "/ui/login"},
    }
    return create_json_response(data)


@app.route("/login", methods=["POST"])
def login():
    """Аутентифицирует пользователя по Basic Auth и возвращает JWT."""
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return create_json_response({"message": "Необходима Basic-аутентификация"}, 401)

    user_data = api_users.get(auth.username)
    if not user_data or not check_password_hash(
        user_data["password_hash"], auth.password
    ):
        return create_json_response(
            {"message": "Неверное имя пользователя или пароль"}, 401
        )

    token = jwt.encode(
        {
            "user": auth.username,
            "role": user_data["role"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        },
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )

    return create_json_response({"token": token})


@app.route("/api/client/scooters", methods=["GET"])
@token_required
def get_available_scooters(current_user):
    """Возвращает список доступных самокатов. Доступно только для роли 'client'."""
    if current_user["role"] != "client":
        return create_json_response(
            {"message": "Доступ запрещен: функция только для клиентов"}, 403
        )

    session = get_session(current_user["db_user"], current_user["db_pass"])
    if not session:
        return create_json_response({"message": "Ошибка подключения к БД"}, 500)

    try:
        query = text("SELECT * FROM public.available_scooters")
        scooters_data = session.execute(query).fetchall()

        result = []
        for row in scooters_data:
            row_dict = dict(row._mapping)
            for key, value in row_dict.items():
                if isinstance(value, Decimal):
                    row_dict[key] = float(value)
            result.append(row_dict)

        return create_json_response(result)
    except Exception as e:
        print(f"Error in get_available_scooters: {e}")
        return create_json_response(
            {"message": "Внутренняя ошибка сервера при выполнении запроса"}, 500
        )
    finally:
        if session:
            session.close()


@app.route("/api/tech/maintenance_log", methods=["GET"])
@token_required
def get_maintenance_log(current_user):
    """Возвращает журнал ТО. Доступно только для роли 'technician'."""
    if current_user["role"] != "technician":
        return create_json_response(
            {"message": "Доступ запрещен: функция только для техников"}, 403
        )

    session = get_session(current_user["db_user"], current_user["db_pass"])
    if not session:
        return create_json_response({"message": "Ошибка подключения к БД"}, 500)

    try:
        query = text("SELECT * FROM public.maintenance_log")
        logs_data = session.execute(query).fetchall()

        result = []
        for row in logs_data:
            row_dict = dict(row._mapping)
            for key, value in row_dict.items():
                if isinstance(value, datetime.date):
                    row_dict[key] = value.isoformat()
            result.append(row_dict)

        return create_json_response(result)
    except Exception as e:
        print(f"Error in get_maintenance_log: {e}")
        return create_json_response(
            {"message": "Внутренняя ошибка сервера при выполнении запроса"}, 500
        )
    finally:
        if session:
            session.close()
