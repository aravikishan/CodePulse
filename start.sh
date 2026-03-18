#!/usr/bin/env bash
set -e

echo "============================================"
echo "  CodePulse - Python Code Analysis Tool"
echo "  Starting on port 8000..."
echo "============================================"

export CODEPULSE_PORT=8000

# Create instance directory for SQLite
mkdir -p instance

# Run with gunicorn in production, fallback to Flask dev server
if command -v gunicorn &> /dev/null; then
    echo "Starting with gunicorn..."
    gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 120 "app:app"
else
    echo "Starting with Flask development server..."
    python app.py
fi
