#!/bin/bash

# URL для скачивания
URL="https://f933fcdf-16c7-4fad-a2b2-f0fed09ea533-webtech-partial-content.web.lms.itmo.xyz/download/passwords"

# Итоговый файл, в который будут объединяться части
OUTPUT_FILE="passwords.csv"

# Общий размер файла
FILE_SIZE=73081

# Начальные значения для диапазонов байтов
START=72000
BLOCK_SIZE=5

# Очистить итоговый файл перед загрузкой
> "$OUTPUT_FILE"

# Цикл для скачивания файла частями
while [ $START -lt $FILE_SIZE ]; do
    END=$((START + BLOCK_SIZE - 1))

    # Выполняем curl запрос в фоновом режиме и сразу добавляем данные в итоговый файл
    echo "Скачиваем байты с $START по $END..."
    curl -H "Range: bytes=$START-$END" "$URL" >> "$OUTPUT_FILE" &
    
    # Обновляем начальный байт для следующей части
    START=$((END))

    # Задержка, чтобы не перегружать сервер
    sleep 0.1
done

# Дожидаемся завершения всех фонов
wait

echo "Скачивание завершено. Все данные сохранены в $OUTPUT_FILE."
