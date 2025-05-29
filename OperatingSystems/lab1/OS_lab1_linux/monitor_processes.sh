#!/bin/bash
OUTPUT_FILE="process_count.txt"
echo "Время,Число процессов" > $OUTPUT_FILE

START_TIME=$(date +%s)

while true; do
    PROCESS_COUNT=$(ps aux | wc -l)
    CURRENT_TIME=$(date +%s)
    echo "$(date +%H:%M:%S),$PROCESS_COUNT" >> $OUTPUT_FILE
    if [ $(($CURRENT_TIME - $START_TIME)) -ge 60 ]; then
        break
    fi
    sleep 1
done
