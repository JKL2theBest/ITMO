import requests

# Указание URL, на который нужно отправить запрос
url = "https://093714fc-64d8-4c2f-a945-75bfea3407b5-http-get.web.lms.itmo.xyz/getflag"

# Данные, которые могут быть отправлены в POST запросе
data = {
    "mailbox": "some_value"  # Пример, если требуется передать значение (например, в поле 'mailbox')
}

# Отправка POST-запроса
response = requests.post(url, data=data)

# Проверка успешности запроса
if response.status_code == 200:
    print("Ответ от сервера:", response.text)
else:
    print("Ошибка:", response.status_code)
