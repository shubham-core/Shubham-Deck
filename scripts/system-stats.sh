#!/bin/bash

CPU=$(top -bn1 | awk '/Cpu\(s\)/ {print 100 - $8 "%"}')

RAM=$(free -h | awk '/Mem:/ {print $3 " / " $2}')

DISK=$(df -h / | awk 'NR==2 {print $3 " / " $2 " (" $5 ")"}')

UPTIME=$(uptime -p)

TEMP=$(sensors 2>/dev/null | awk '/Package id 0:/ {print $4; exit}')

if [ -z "$TEMP" ]; then
    TEMP="N/A"
fi

notify-send \
    "Shubham Deck — System Stats" \
    "CPU: $CPU
RAM: $RAM
Disk: $DISK
CPU Temp: $TEMP
Uptime: $UPTIME"
