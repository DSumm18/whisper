# Whisper Voice Typing Suite

A comprehensive voice typing solution with two main components:

1. **Desktop App** - Always-on voice typing tool for your laptop
2. **STT Library** - Reusable speech-to-text component for web/mobile apps

## Components

### 1. Desktop Voice Typing App (`/desktop-app`)
- Always visible at bottom of screen
- Global hotkey activation (Ctrl+Shift+V)
- Local Whisper transcription (100% free)
- Intelligent text cleanup with grammar/punctuation correction
- Types directly into any application

**Features:**
- ✅ System tray integration
- ✅ Offline capable
- ✅ Context-aware text correction
- ✅ Privacy-focused (all local processing)

### 2. STT Library (`/stt-library`)
Reusable JavaScript library for adding speech-to-text to any web or mobile app.

**Features:**
- ✅ Browser Web Speech API (free)
- ✅ Whisper API fallback (paid but cheap)
- ✅ Grammar cleanup (free + paid options)
- ✅ Easy integration
- ✅ TypeScript support

## Quick Start

### Desktop App
```bash
# Install dependencies
cd desktop-app
npm install

cd ../whisper-service
pip install -r requirements.txt

# Run
npm start
```

### STT Library
```bash
cd stt-library
npm install
npm run build

# Use in your app
npm install ./stt-library
```

```javascript
import { startSpeechToText, cleanupText } from 'whisper-stt';

const transcript = await startSpeechToText();
const cleaned = await cleanupText(transcript);
```

## Cost Analysis

### Desktop App: **FREE**
- Local Whisper models
- Optional: Ollama for text cleanup (free)
- Optional: Claude API for better cleanup (~$0.001/use)

### STT Library: **FREE or Pay-as-you-go**
- Browser API: Free
- Whisper API: $0.006/minute
- Grammar cleanup: Free (basic) or $0.001-0.003 (advanced)

## Architecture

```
┌─────────────────────────────────────┐
│     Desktop App (Electron)          │
│  ┌──────────────────────────────┐   │
│  │  UI (Bottom screen overlay)  │   │
│  └──────────────────────────────┘   │
│              ↓                       │
│  ┌──────────────────────────────┐   │
│  │  Python Whisper Service      │   │
│  │  (Local STT processing)      │   │
│  └──────────────────────────────┘   │
│              ↓                       │
│  ┌──────────────────────────────┐   │
│  │  Text Cleanup (Ollama/API)   │   │
│  └──────────────────────────────┘   │
│              ↓                       │
│  ┌──────────────────────────────┐   │
│  │  Keyboard Simulation         │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│      STT Library (NPM Package)      │
│  ┌──────────────────────────────┐   │
│  │  Browser Speech API          │   │
│  │  (Primary - Free)            │   │
│  └──────────────────────────────┘   │
│              ↓                       │
│  ┌──────────────────────────────┐   │
│  │  Whisper API Fallback        │   │
│  │  (Optional - Paid)           │   │
│  └──────────────────────────────┘   │
│              ↓                       │
│  ┌──────────────────────────────┐   │
│  │  Grammar Cleanup Utils       │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

## Requirements

### Desktop App
- Node.js 18+
- Python 3.8+
- 4GB RAM minimum (8GB recommended for larger Whisper models)
- Linux/Windows/macOS

### STT Library
- Node.js 16+
- Modern browser with Web Speech API support
- (Optional) OpenAI API key for Whisper fallback

## License

MIT
