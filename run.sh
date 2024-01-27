#!/bin/bash

sleep $(( ( RANDOM % 90 ) + 120 ))m
cd /app && python3 get_paper.py > /proc/1/fd/1 2>/proc/1/fd/2
