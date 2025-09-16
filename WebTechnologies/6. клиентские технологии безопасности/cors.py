from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Разрешить CORS со всех источников


@app.route("/")
def hello():
    return "CORS включен!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=11000)
