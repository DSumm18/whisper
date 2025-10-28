#!/usr/bin/env python3
"""
Whisper Voice Typing Backend Service

This Flask server provides speech-to-text transcription using OpenAI Whisper
and optional text cleanup using LLM APIs (Claude, GPT) or local Ollama.
"""

import os
import io
import wave
import time
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
import whisper
import pyaudio
import numpy as np
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'base')  # tiny, base, small, medium, large
CLEANUP_METHOD = os.getenv('CLEANUP_METHOD', 'basic')  # basic, ollama, claude, openai
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')

# Load Whisper model
print(f"Loading Whisper model: {WHISPER_MODEL}")
model = whisper.load_model(WHISPER_MODEL)
print("Whisper model loaded!")

# Audio recording state
audio_frames = []
is_recording = False
audio_stream = None
pyaudio_instance = None

# Audio configuration
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'whisper_model': WHISPER_MODEL,
        'cleanup_method': CLEANUP_METHOD
    })


@app.route('/start-recording', methods=['POST'])
def start_recording():
    """Start recording audio from microphone"""
    global is_recording, audio_frames, audio_stream, pyaudio_instance

    if is_recording:
        return jsonify({'error': 'Already recording'}), 400

    audio_frames = []
    is_recording = True

    try:
        # Initialize PyAudio
        pyaudio_instance = pyaudio.PyAudio()
        audio_stream = pyaudio_instance.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            stream_callback=audio_callback
        )

        audio_stream.start_stream()

        return jsonify({
            'status': 'recording',
            'message': 'Recording started'
        })

    except Exception as e:
        is_recording = False
        return jsonify({'error': str(e)}), 500


def audio_callback(in_data, frame_count, time_info, status):
    """Callback for audio stream"""
    global audio_frames
    if is_recording:
        audio_frames.append(in_data)
    return (in_data, pyaudio.paContinue)


@app.route('/stop-recording', methods=['POST'])
def stop_recording():
    """Stop recording and transcribe audio"""
    global is_recording, audio_frames, audio_stream, pyaudio_instance

    if not is_recording:
        return jsonify({'error': 'Not recording'}), 400

    is_recording = False

    try:
        # Stop and close the stream
        if audio_stream:
            audio_stream.stop_stream()
            audio_stream.close()
        if pyaudio_instance:
            pyaudio_instance.terminate()

        # Save audio to temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_filename = temp_file.name

            # Write WAV file
            with wave.open(temp_filename, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(pyaudio_instance.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(audio_frames))

        # Transcribe with Whisper
        print("Transcribing with Whisper...")
        result = model.transcribe(temp_filename)
        transcript = result['text'].strip()

        # Clean up temporary file
        os.unlink(temp_filename)

        print(f"Transcript: {transcript}")

        # Clean up text
        cleaned_text = cleanup_text(transcript)
        print(f"Cleaned: {cleaned_text}")

        return jsonify({
            'status': 'success',
            'transcript': transcript,
            'cleaned_text': cleaned_text
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def cleanup_text(text):
    """Clean up transcribed text with punctuation, grammar, and context awareness"""

    if CLEANUP_METHOD == 'basic':
        return basic_cleanup(text)
    elif CLEANUP_METHOD == 'ollama':
        return ollama_cleanup(text)
    elif CLEANUP_METHOD == 'claude':
        return claude_cleanup(text)
    elif CLEANUP_METHOD == 'openai':
        return openai_cleanup(text)
    else:
        return text


def basic_cleanup(text):
    """Basic punctuation and capitalization cleanup"""
    if not text:
        return text

    # Capitalize first letter
    text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()

    # Add period at the end if no punctuation
    if text and text[-1] not in '.!?':
        text += '.'

    return text


def ollama_cleanup(text):
    """Use local Ollama for intelligent text cleanup"""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "llama3",
                "prompt": f"""Fix grammar, add proper punctuation, and correct any misheard words based on context.
Keep the meaning intact. Only return the corrected text, nothing else.

Text: {text}

Corrected:""",
                "stream": False
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return result.get('response', text).strip()
        else:
            print(f"Ollama error: {response.status_code}")
            return basic_cleanup(text)

    except Exception as e:
        print(f"Ollama cleanup failed: {e}")
        return basic_cleanup(text)


def claude_cleanup(text):
    """Use Claude API for intelligent text cleanup"""
    if not CLAUDE_API_KEY:
        print("Claude API key not found, using basic cleanup")
        return basic_cleanup(text)

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1024,
                "messages": [{
                    "role": "user",
                    "content": f"""Fix grammar, add proper punctuation, and correct any misheard words based on context.
Keep the meaning intact. Only return the corrected text, nothing else.

Text: {text}"""
                }]
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return result['content'][0]['text'].strip()
        else:
            print(f"Claude API error: {response.status_code}")
            return basic_cleanup(text)

    except Exception as e:
        print(f"Claude cleanup failed: {e}")
        return basic_cleanup(text)


def openai_cleanup(text):
    """Use OpenAI GPT for intelligent text cleanup"""
    if not OPENAI_API_KEY:
        print("OpenAI API key not found, using basic cleanup")
        return basic_cleanup(text)

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{
                    "role": "user",
                    "content": f"""Fix grammar, add proper punctuation, and correct any misheard words based on context.
Keep the meaning intact. Only return the corrected text, nothing else.

Text: {text}"""
                }],
                "max_tokens": 500
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            print(f"OpenAI API error: {response.status_code}")
            return basic_cleanup(text)

    except Exception as e:
        print(f"OpenAI cleanup failed: {e}")
        return basic_cleanup(text)


if __name__ == '__main__':
    print("="*50)
    print("Whisper Voice Typing Service")
    print("="*50)
    print(f"Model: {WHISPER_MODEL}")
    print(f"Cleanup method: {CLEANUP_METHOD}")
    print(f"Server starting on http://localhost:5000")
    print("="*50)

    app.run(host='0.0.0.0', port=5000, debug=False)
