from app import app

if __name__ == "__main__":
    # debug=True никогда не должен использоваться в реальном (production) приложении.
    # Это уязвимость, так как может раскрыть внутреннюю структуру кода при ошибке.
    app.run(debug=True, port=5000)
