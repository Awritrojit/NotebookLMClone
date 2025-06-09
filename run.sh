#!/bin/bash

# Setup and run NotebookLM Clone

echo "==============================================="
echo "Setting up NotebookLM Clone"
echo "==============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "WARNING: No .env file found."
    echo "Please create a .env file with your Gemini API key:"
    echo "GEMINI_API_KEY=your_key_here"
fi

# Ensure data directory exists
mkdir -p data

echo "==============================================="
echo "Starting NotebookLM Clone"
echo "==============================================="

# Run the application
python app/app.py
