# Whisper STT Library

Reusable JavaScript library for adding speech-to-text to web and mobile applications.

## Features

- 🎤 **Browser Web Speech API** (100% FREE)
- 🌐 **OpenAI Whisper API** fallback (paid, $0.006/min)
- ✨ **Grammar cleanup** (free + paid options)
- 📱 **Works everywhere** - Web, React, Vue, mobile webviews
- 🔄 **Auto-fallback** - Seamless switching between methods
- 🎯 **TypeScript ready**

## Installation

```bash
npm install whisper-stt
```

Or use directly in your project:

```bash
# From this repository
npm install ../stt-library
```

## Quick Start

### Basic Usage (Free - Browser API)

```javascript
import { init, startSpeechToText, cleanup } from 'whisper-stt';

// Optional: Initialize with config
init({
  language: 'en-US',
  continuous: false,
  interimResults: false
});

// Start speech recognition
const transcript = await startSpeechToText();
console.log('You said:', transcript);

// Clean up the text
const cleaned = await cleanup(transcript);
console.log('Cleaned:', cleaned);
```

### With Whisper API Fallback

```javascript
import { init, startSpeechToText } from 'whisper-stt';

init({
  preferredMethod: 'browser',
  autoFallback: true,
  whisperApiKey: 'your-openai-api-key' // For fallback
});

const transcript = await startSpeechToText();
```

### Continuous Listening

```javascript
import { createContinuousSession } from 'whisper-stt';

const session = createContinuousSession({
  language: 'en-US',
  onFinal: (text) => {
    console.log('Final:', text);
  },
  onInterim: (text) => {
    console.log('Interim:', text);
  }
});

// Start listening
session.start();

// Stop when done
const fullTranscript = session.stop();
```

### Advanced Cleanup

```javascript
import { cleanup } from 'whisper-stt';

// Basic cleanup (free)
const cleaned = await cleanup(transcript, {
  cleanupMethod: 'basic'
});

// LanguageTool (free with limits)
const cleaned = await cleanup(transcript, {
  cleanupMethod: 'languagetool'
});

// Claude API (best quality, ~$0.001 per cleanup)
const cleaned = await cleanup(transcript, {
  cleanupMethod: 'claude',
  claudeApiKey: 'your-claude-api-key'
});

// OpenAI GPT (~$0.002 per cleanup)
const cleaned = await cleanup(transcript, {
  cleanupMethod: 'openai',
  openaiApiKey: 'your-openai-api-key'
});
```

## React Example

```jsx
import React, { useState } from 'react';
import { startSpeechToText, cleanup } from 'whisper-stt';

function VoiceInput() {
  const [text, setText] = useState('');
  const [isRecording, setIsRecording] = useState(false);

  const handleVoiceInput = async () => {
    setIsRecording(true);

    try {
      const transcript = await startSpeechToText();
      const cleaned = await cleanup(transcript);
      setText(cleaned);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsRecording(false);
    }
  };

  return (
    <div>
      <button onClick={handleVoiceInput} disabled={isRecording}>
        {isRecording ? 'Listening...' : 'Start Voice Input'}
      </button>
      <textarea value={text} onChange={(e) => setText(e.target.value)} />
    </div>
  );
}
```

## Vue Example

```vue
<template>
  <div>
    <button @click="startVoiceInput" :disabled="isRecording">
      {{ isRecording ? 'Listening...' : 'Start Voice Input' }}
    </button>
    <textarea v-model="text"></textarea>
  </div>
</template>

<script>
import { ref } from 'vue';
import { startSpeechToText, cleanup } from 'whisper-stt';

export default {
  setup() {
    const text = ref('');
    const isRecording = ref(false);

    const startVoiceInput = async () => {
      isRecording.value = true;

      try {
        const transcript = await startSpeechToText();
        const cleaned = await cleanup(transcript);
        text.value = cleaned;
      } catch (error) {
        console.error('Error:', error);
      } finally {
        isRecording.value = false;
      }
    };

    return { text, isRecording, startVoiceInput };
  }
};
</script>
```

## Configuration Options

```javascript
init({
  // Preferred method: 'browser' or 'whisper-api'
  preferredMethod: 'browser',

  // Auto-fallback if preferred method fails
  autoFallback: true,

  // API keys (optional)
  whisperApiKey: null,
  claudeApiKey: null,
  openaiApiKey: null,

  // Language (BCP 47 format)
  language: 'en-US',

  // Continuous mode
  continuous: true,

  // Show interim results
  interimResults: true,

  // Cleanup method: 'basic', 'languagetool', 'claude', 'openai'
  cleanupMethod: 'basic'
});
```

## API Reference

### `init(options)`
Initialize the library with configuration.

### `startSpeechToText(options?)`
Start speech recognition. Returns a promise with the transcript.

### `recordAndTranscribe(duration?)`
Record for a specific duration and transcribe.

### `cleanup(text, options?)`
Clean up transcribed text with grammar/punctuation correction.

### `createContinuousSession(config)`
Create a continuous listening session with manual control.

### `isBrowserAPIAvailable()`
Check if Browser Speech API is available.

## Browser Support

- ✅ Chrome/Edge (Web Speech API)
- ✅ Safari (Web Speech API)
- ⚠️ Firefox (limited support, use Whisper API fallback)
- ✅ All modern browsers (with Whisper API)

## Cost Breakdown

### Free Options
- Browser Web Speech API: **$0**
- Basic cleanup: **$0**
- LanguageTool: **$0** (20 requests/min limit)

### Paid Options
- Whisper API: **$0.006/minute** (~$0.10 per hour)
- Claude cleanup: **~$0.001/cleanup**
- OpenAI cleanup: **~$0.002/cleanup**

**Example:** 100 voice inputs/month
- Free: $0
- Whisper API (1 min each): $0.60
- With Claude cleanup: $0.70 total

## License

MIT
