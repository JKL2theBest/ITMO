#!/bin/bash

DISC="sda"
cat /sys/block/$DISC/queue/scheduler
for T in kyber bfq none mq-deadline; do
    echo $T > /sys/block/$DISC/queue/scheduler
    cat /sys/block/$DISC/queue/scheduler
    sync && /sbin/hdparm -tT /dev/$DISC && echo "----"
    sleep 15
done
