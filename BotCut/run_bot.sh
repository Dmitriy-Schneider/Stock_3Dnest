#!/bin/bash

# BotCut Launch Script for Linux/Mac

echo "=========================================="
echo "Starting BotCut Telegram Bot"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please copy EnvExample.txt to .env and configure it."
    echo ""
    exit 1
fi

# Check if HPMCut server is running
echo "Checking HPMCut server..."
if ! curl -s http://127.0.0.1:3001/ > /dev/null 2>&1; then
    echo "WARNING: HPMCut server is not running!"
    echo "Please start server_fastapi.py first."
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "Starting bot..."
echo ""

python3 main.py
