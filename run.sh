#!/bin/bash

sleep $(( ( RANDOM % 180 )  + 1 ))
cd /app && python3 get_paper.py
