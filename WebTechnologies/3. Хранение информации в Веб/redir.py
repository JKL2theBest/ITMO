import requests

# Установим начальный URL
url = "http://10.10.10.10:32773/promo"


# Функция для обработки редиректов
def handle_redirects(url):
    visited_urls = set()  # Множество для хранения посещенных URL
    redirect_count = 0  # Счётчик редиректов
    while url:
        if url in visited_urls:
            print(f"Циклический редирект найден! Прервано на {url}")
            break
        visited_urls.add(url)
        print(f"Перенаправление на: {url}")

        response = requests.get(
            url, allow_redirects=False
        )  # Запрос без автоматических редиректов
        if (
            response.status_code == 301
            or response.status_code == 302
            or response.status_code == 303
        ):
            # Если редирект, извлекаем новый URL
            location = response.headers.get("Location")
            if location:
                redirect_count += 1  # Увеличиваем счётчик редиректов
                if location.startswith("http"):  # Абсолютный URL
                    url = location
                else:  # Относительный URL
                    url = "http://10.10.10.10:32773" + location
            else:
                print("Ошибка: отсутствует поле Location в заголовках.")
                break
        else:
            print(f"Запрос завершен. Код ответа: {response.status_code}")
            break

    print(f"Общее количество редиректов: {redirect_count}")


# Вызовем функцию для обработки редиректов
handle_redirects(url)
