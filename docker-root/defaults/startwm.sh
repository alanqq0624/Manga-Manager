#!/bin/bash
/startpulse.sh &
/usr/bin/startxfce4 > /dev/null 2>&1
python /app/main.py