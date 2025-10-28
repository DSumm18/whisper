# Quick Test Guide - Run on Your Laptop

## 🚀 Quick Start (5 minutes)

### Option 1: Automated Test (Recommended)

```bash
cd /path/to/whisper
./test-desktop-app.sh
```

This script will:
1. Check prerequisites
2. Install all dependencies
3. Start both services
4. Give you usage instructions

### Option 2: Manual Test

**Terminal 1 - Start Backend:**
```bash
cd whisper-service
pip3 install -r requirements.txt
python3 whisper_server.py
```

Wait for: `"Whisper model loaded!"` message

**Terminal 2 - Start Desktop App:**
```bash
cd desktop-app
npm install
npm start
```

---

## 🎤 How to Test

1. **Look for the system tray icon** (purple/blue circle)

2. **Press `Ctrl+Shift+V`** to start recording
   - UI will appear at bottom of screen
   - Red indicator shows recording

3. **Speak clearly:**
   - "Hello this is a test of the voice typing system"
   - "I want to see if it adds punctuation correctly"

4. **Press `Ctrl+Shift+V` again** to stop

5. **Watch the magic!**
   - Text appears in the overlay
   - Gets typed into your active application
   - Punctuation added automatically

---

## ✅ What to Verify

### Basic Functionality:
- [ ] App starts without errors
- [ ] System tray icon appears
- [ ] Press Ctrl+Shift+V shows overlay
- [ ] Microphone records audio
- [ ] Transcription appears
- [ ] Text is typed into application

### Text Quality:
- [ ] Punctuation added automatically
- [ ] First letter capitalized
- [ ] Misheard words corrected (if using smart cleanup)
- [ ] Output makes sense

### Performance:
- [ ] Recording starts immediately
- [ ] Transcription completes in 2-5 seconds
- [ ] No lag when typing text

---

## 🧪 Test Scenarios

### Test 1: Simple Sentence
**Say:** "Hello world this is a test"
**Expected:** "Hello world, this is a test."

### Test 2: Question
**Say:** "What time is it"
**Expected:** "What time is it?"

### Test 3: Complex Sentence
**Say:** "I need to buy eggs milk bread and cheese from the store"
**Expected:** "I need to buy eggs, milk, bread, and cheese from the store."

### Test 4: Context Correction
**Say:** "Their going to the store" (intentionally wrong)
**Expected (with smart cleanup):** "They're going to the store."

---

## 🔧 Testing Different Cleanup Methods

Edit `whisper-service/.env`:

### Basic (Free):
```
CLEANUP_METHOD=basic
```
Simple punctuation only

### Ollama (Free, Smart):
```
CLEANUP_METHOD=ollama
```
Requires: `ollama serve` running with a model installed

### Claude API (Best Quality):
```
CLEANUP_METHOD=claude
CLAUDE_API_KEY=your_key_here
```

### OpenAI (Good Quality):
```
CLEANUP_METHOD=openai
OPENAI_API_KEY=your_key_here
```

Restart backend after changing `.env`

---

## 📱 Testing the STT Library (Web)

Open the web example:

```bash
cd examples
python3 -m http.server 8000
```

Visit: http://localhost:8000/web-example.html

**Test:**
1. Click "Start Speaking"
2. Grant microphone permission
3. Speak clearly
4. Text appears in real-time!
5. Try different cleanup methods

---

## 🐛 Common Issues

### "No module named 'pyaudio'"
```bash
# Ubuntu/Debian:
sudo apt-get install portaudio19-dev python3-pyaudio
pip3 install pyaudio

# macOS:
brew install portaudio
pip3 install pyaudio
```

### "Whisper service not running"
- Check backend terminal for errors
- Visit http://localhost:5000/health
- Make sure port 5000 is not in use

### "No microphone access"
- Check system settings → Privacy → Microphone
- Grant permission to Terminal/Electron
- Test mic with: `arecord -l` (Linux)

### App doesn't start
```bash
# Clean install
rm -rf desktop-app/node_modules
cd desktop-app
npm install
npm start
```

### Text not typing
- Click into a text field first
- Check if Ctrl+Shift+V is captured by another app
- Try changing the hotkey in main.js

---

## 📊 Performance Benchmarks

Expected times (on decent laptop):

| Model | Load Time | Transcribe 10s |
|-------|-----------|----------------|
| tiny  | 5-10s     | 1-2s          |
| base  | 10-15s    | 2-3s          |
| small | 15-20s    | 3-5s          |
| medium| 20-30s    | 5-8s          |
| large | 30-60s    | 8-15s         |

Start with **base** model (default).

---

## 🎯 Success Criteria

Your app is working correctly if:

✅ Records voice with hotkey
✅ Transcribes accurately (90%+ words correct)
✅ Adds punctuation automatically
✅ Types into any application
✅ No crashes or freezes
✅ Responds within 5 seconds

---

## 📸 Screenshot Your Results

When testing, capture:
1. System tray icon
2. Recording overlay
3. Transcribed text
4. Final typed output

---

## 🚀 Next Steps After Testing

If everything works:

1. **Customize hotkey** (edit `desktop-app/main.js`)
2. **Try better models** (edit `.env`: WHISPER_MODEL=small)
3. **Add smart cleanup** (setup Ollama or API keys)
4. **Build distributable** (`npm run build:linux`)
5. **Integrate STT library** into your other apps!

---

## 💬 Need Help?

If something doesn't work:
1. Check the terminal output for errors
2. Test microphone with other apps first
3. Verify all dependencies installed
4. Try the web example (simpler test)
5. Check SETUP.md for detailed troubleshooting

---

**Ready to test?** Run `./test-desktop-app.sh` and start voice typing! 🎤
