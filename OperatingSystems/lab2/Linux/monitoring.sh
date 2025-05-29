#!/bin/bash
echo "Time,FreeMemory(kB)" > memory_log.csv
./membomb &
BOMB_PID=$!
while kill -0 $BOMB_PID 2> /dev/null; do
    free_mem=$(free | grep Mem | awk '{print $4}')
    echo "$(date +%s),$free_mem" >> memory_log.csv
    sleep 2
done