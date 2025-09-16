"""import requests
import json

url = 'https://c217ef3a-9aea-4314-823a-8e1e27886d62-datatransfer.web.lms.itmo.xyz/api/books'
headers = {'Content-Type': 'application/json'}
data = {
    'title': 'Название',
    'author': 'Автор'
}

response = requests.post(url, headers=headers, json=data)

print('Статус код:', response.status_code)
print('Ответ сервера:', response.text)

import requests
import json

book_id = 2  # Идентификатор книги, которую нужно обновить
url = f'https://c217ef3a-9aea-4314-823a-8e1e27886d62-datatransfer.web.lms.itmo.xyz/api/books/{book_id}'
headers = {'Content-Type': 'application/json'}
data = {
    'title': 'Новое Название',
    'author': 'Новый Автор'
}

response = requests.put(url, headers=headers, json=data)

print('Статус код:', response.status_code)
print('Ответ сервера:', response.text)

import requests
import json

book_id = 2  # Идентификатор книги, которую нужно частично обновить
url = f'https://c217ef3a-9aea-4314-823a-8e1e27886d62-datatransfer.web.lms.itmo.xyz/api/books/{book_id}'
headers = {'Content-Type': 'application/json'}
data = {
    'title': 'Обновленное Название'
}

response = requests.patch(url, headers=headers, json=data)

print('Статус код:', response.status_code)
print('Ответ сервера:', response.text)
"""

import requests

url = "https://c217ef3a-9aea-4314-823a-8e1e27886d62-datatransfer.web.lms.itmo.xyz/api/flag"  # Замените на актуальный URL
response = requests.get(url)

if response.status_code == 200:
    print("Флаг:", response.text)
else:
    print("Ошибка:", response.status_code)
