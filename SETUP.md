# Setup Guide

Complete setup instructions for both components.

## Desktop App Setup

### Prerequisites

1. **Node.js 18+**
   ```bash
   node --version  # Should be 18.x or higher
   ```

2. **Python 3.8+**
   ```bash
   python3 --version  # Should be 3.8 or higher
   ```

3. **System dependencies (Linux)**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install portaudio19-dev python3-pyaudio

   # Fedora
   sudo dnf install portaudio-devel

   # Arch
   sudo pacman -S portaudio
   ```

### Installation Steps

#### 1. Install Desktop App Dependencies

```bash
cd desktop-app
npm install
```

#### 2. Install Python Backend Dependencies

```bash
cd ../whisper-service
pip3 install -r requirements.txt
```

This will download the Whisper model (~140MB for 'base' model).

#### 3. Configure (Optional)

```bash
cd whisper-service
cp .env.example .env
nano .env  # Edit configuration
```

**Configuration options:**
- `WHISPER_MODEL`: tiny, base, small, medium, large
  - tiny (39M): Fast, lower accuracy
  - base (74M): Good balance (recommended)
  - small (244M): Better accuracy
  - medium (769M): Very good accuracy
  - large (1550M): Best accuracy, slow

- `CLEANUP_METHOD`: basic, ollama, claude, openai
  - basic: Free, simple punctuation
  - ollama: Free, needs local Ollama
  - claude: Paid API, best quality
  - openai: Paid API, good quality

#### 4. Run the Application

**Terminal 1 - Start Python backend:**
```bash
cd whisper-service
python3 whisper_server.py
```

**Terminal 2 - Start Electron app:**
```bash
cd desktop-app
npm start
```

### Usage

1. The app will start with a system tray icon
2. Press **Ctrl+Shift+V** to start recording
3. Speak naturally
4. Press **Ctrl+Shift+V** again to stop and transcribe
5. Text will be typed into your active application

### Troubleshooting

**"No module named 'pyaudio'"**
```bash
# Linux
sudo apt-get install portaudio19-dev
pip3 install pyaudio

# macOS
brew install portaudio
pip3 install pyaudio

# Windows
pip3 install pipwin
pipwin install pyaudio
```

**"Whisper service not running"**
- Make sure Python backend is running first
- Check http://localhost:5000/health in browser

**"No microphone access"**
- Grant microphone permissions in system settings
- Check microphone with: `arecord -l` (Linux) or system preferences

---

## STT Library Setup

### For Web Projects

#### 1. Install

```bash
npm install ../stt-library
# Or from npm when published:
# npm install whisper-stt
```

#### 2. Use in Your App

```javascript
import { init, startSpeechToText, cleanup } from 'whisper-stt';

// Initialize (optional)
init({
  language: 'en-US',
  cleanupMethod: 'basic'
});

// Use in your app
async function handleVoiceInput() {
  try {
    const transcript = await startSpeechToText();
    const cleaned = await cleanup(transcript);
    return cleaned;
  } catch (error) {
    console.error('Voice input failed:', error);
  }
}
```

#### 3. Add API Keys (Optional)

For advanced features, create a `.env` file:

```bash
# Whisper API (for fallback)
WHISPER_API_KEY=sk-...

# Text cleanup (optional)
CLAUDE_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

### Browser Compatibility

- ✅ Chrome/Edge: Full support
- ✅ Safari: Full support
- ⚠️ Firefox: Limited, use Whisper API fallback
- ✅ Mobile browsers: Varies, test on target devices

### Testing

Open the example in your browser:

```bash
cd examples
python3 -m http.server 8000
# Visit: http://localhost:8000/web-example.html
```

---

## Optional: Ollama for Free Text Cleanup

If you want FREE intelligent text cleanup without API costs:

### 1. Install Ollama

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama

# Windows
# Download from https://ollama.com/download
```

### 2. Download a Model

```bash
ollama pull llama3
# Or: ollama pull mistral
```

### 3. Configure

```bash
cd whisper-service
nano .env
```

Set:
```
CLEANUP_METHOD=ollama
OLLAMA_URL=http://localhost:11434
```

### 4. Start Ollama

```bash
ollama serve
```

Now your desktop app will use local AI for text cleanup!

---

## Development

### Desktop App

```bash
cd desktop-app
npm run dev  # Development mode with hot reload
npm run build  # Build for production
npm run build:linux  # Build Linux package
npm run build:win  # Build Windows package
npm run build:mac  # Build macOS package
```

### STT Library

```bash
cd stt-library
npm run build  # Build for distribution
npm run dev  # Watch mode for development
```

---

## Cost Estimation

### Desktop App (100% Free Setup)
- Whisper: Local, $0
- Text cleanup: Basic or Ollama, $0
- **Total: $0/month**

### Desktop App (Paid Cleanup)
- Whisper: Local, $0
- Text cleanup: Claude API, ~$3-5/month for heavy use
- **Total: ~$3-5/month**

### STT Library (Web Apps)
- Browser API: $0
- Whisper API fallback: $0.006/min
- Text cleanup: $0.001-0.003/cleanup
- **Typical: $0.50-2/user/month**

---

## Next Steps

1. ✅ Test the desktop app with voice input
2. ✅ Try the web example
3. ✅ Integrate STT library into your apps
4. ✅ Customize cleanup methods based on your needs
5. ✅ Build and deploy!

For issues or questions, check the main README.md or open an issue.
