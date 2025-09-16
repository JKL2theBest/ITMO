from flask import Flask, session, jsonify

# Флаг для возврата администратору
flag = "YOUR_FLAG_HERE"

# Инициализация приложения Flask
app = Flask(__name__)

# Секретный ключ для подписи сессий
app.secret_key = "UGd78t3487ry384rrf4387ftg37"


@app.route("/app.py")
def source():
    return open("app.py", "r").read()


@app.route("/")
def index():
    if "username" not in session:
        session["username"] = "Guest"
    if session["username"] == "admin":
        return flag
    return jsonify(session["username"]), 200


if __name__ == "__main__":
    app.run(debug=True)
