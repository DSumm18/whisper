#!/bin/bash

# Whisper Voice Typing - Complete Test Script
# Run this on your local machine to test the desktop app

echo "======================================"
echo "Whisper Voice Typing - Test Script"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "Checking prerequisites..."
echo ""

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓${NC} Node.js installed: $NODE_VERSION"
else
    echo -e "${RED}✗${NC} Node.js not found. Please install Node.js 18+ from https://nodejs.org"
    exit 1
fi

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} Python installed: $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Check pip
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} pip3 installed"
else
    echo -e "${RED}✗${NC} pip3 not found. Please install pip3"
    exit 1
fi

echo ""
echo "======================================"
echo "Step 1: Installing Desktop App"
echo "======================================"
echo ""

cd desktop-app
if [ ! -d "node_modules" ]; then
    echo "Installing Electron and dependencies..."
    npm install
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Desktop app dependencies installed"
    else
        echo -e "${RED}✗${NC} Failed to install desktop app dependencies"
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} Desktop app dependencies already installed"
fi
cd ..

echo ""
echo "======================================"
echo "Step 2: Installing Python Backend"
echo "======================================"
echo ""

cd whisper-service

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo -e "${GREEN}✓${NC} Created .env file with default settings"
    echo -e "${YELLOW}Note: Using 'basic' cleanup method (free). Edit .env to change.${NC}"
fi

# Install Python packages
echo "Installing Whisper and dependencies (this may take a few minutes)..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Python dependencies installed"
else
    echo -e "${RED}✗${NC} Failed to install Python dependencies"
    echo "You may need to install system packages first:"
    echo "  Ubuntu/Debian: sudo apt-get install portaudio19-dev python3-pyaudio"
    echo "  macOS: brew install portaudio"
    exit 1
fi

cd ..

echo ""
echo "======================================"
echo "Step 3: Starting Services"
echo "======================================"
echo ""

echo "Starting Python Whisper backend..."
cd whisper-service
python3 whisper_server.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "Waiting for backend to initialize..."
sleep 3

# Check if backend is running
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend is running on http://localhost:5000"
else
    echo -e "${YELLOW}⚠${NC} Backend might still be loading Whisper model..."
    echo "This can take 30-60 seconds for first run."
fi

echo ""
echo "Starting Electron desktop app..."
cd desktop-app
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "======================================"
echo "Services Started!"
echo "======================================"
echo ""
echo -e "${GREEN}✓${NC} Python backend PID: $BACKEND_PID"
echo -e "${GREEN}✓${NC} Electron app PID: $FRONTEND_PID"
echo ""
echo "======================================"
echo "How to Use:"
echo "======================================"
echo ""
echo "1. Look for the Whisper icon in your system tray"
echo "2. Press ${GREEN}Ctrl+Shift+V${NC} to start recording"
echo "3. Speak clearly into your microphone"
echo "4. Press ${GREEN}Ctrl+Shift+V${NC} again to stop and transcribe"
echo "5. Text will be typed into your active application!"
echo ""
echo "======================================"
echo "Troubleshooting:"
echo "======================================"
echo ""
echo "If nothing happens:"
echo "  1. Check microphone permissions in system settings"
echo "  2. Visit http://localhost:5000/health to verify backend"
echo "  3. Check logs in the terminal"
echo ""
echo "To stop services:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Or run: pkill -f 'whisper_server.py' && pkill -f 'electron'"
echo ""
echo "======================================"
echo ""

# Keep script running
echo "Press Ctrl+C to stop all services"
wait
