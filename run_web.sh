#!/bin/bash

echo "Setting up Fast Network Scanner Web Interface..."

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installing Flask..."
    pip3 install flask==2.3.3
fi

echo "Starting web server..."
echo "Open your browser and go to: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py
