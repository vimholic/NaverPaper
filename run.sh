#!/bin/bash

sleep $[ ( $RANDOM % 61 )  + 180 ]m
cd /app && python3 get_paper.py
