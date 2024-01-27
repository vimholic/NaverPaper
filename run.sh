#!/bin/bash

sleep $(( ( RANDOM % 3600 ) + 10800 ))
cd /app && python3 get_paper.py > /proc/1/fd/1 2>/proc/1/fd/2
