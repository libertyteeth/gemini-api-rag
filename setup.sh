#!/bin/bash

# YouTube RAG Tool Setup Script

set -e  # Exit on error

echo "=================================="
echo "YouTube RAG Tool - Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.8 or higher is required"
    echo "Current version: $python_version"
    exit 1
fi
echo "✓ Python $python_version detected"
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt
echo "✓ Python dependencies installed"
echo ""

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium
echo "✓ Playwright browsers installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "IMPORTANT: Edit .env and add your GEMINI_API_KEY, or configure gcloud CLI"
else
    echo "✓ .env file already exists"
fi
echo ""

# Make main.py executable
chmod +x main.py
echo "✓ main.py is now executable"
echo ""

# Check for gcloud
echo "Checking for gcloud CLI..."
if command -v gcloud &> /dev/null; then
    echo "✓ gcloud CLI is installed"
    echo ""
    echo "To use gcloud authentication, run:"
    echo "  gcloud auth application-default login"
else
    echo "! gcloud CLI not found (optional)"
    echo ""
    echo "If you want to use gcloud authentication instead of API key:"
    echo "  1. Install gcloud CLI: https://cloud.google.com/sdk/docs/install"
    echo "  2. Run: gcloud auth application-default login"
fi
echo ""

echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "  1. Configure authentication (choose one):"
echo "     • Edit .env and add GEMINI_API_KEY, OR"
echo "     • Run: gcloud auth application-default login"
echo ""
echo "  2. Run the tool:"
echo "     python main.py"
echo ""
echo "  3. For help:"
echo "     python main.py --help"
echo ""
echo "See README.md for detailed usage instructions."
echo ""
