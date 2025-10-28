/**
 * Whisper STT Library
 *
 * Reusable speech-to-text library with:
 * - Browser Web Speech API (free)
 * - OpenAI Whisper API fallback (paid)
 * - Grammar/punctuation cleanup utilities
 */

import { browserSTT } from './browser-stt';
import { whisperAPI } from './whisper-api';
import { cleanupText } from './grammar-cleanup';

/**
 * Configuration for STT
 */
let config = {
  // Whisper API key (optional - only if using API fallback)
  whisperApiKey: null,

  // Preferred method: 'browser' or 'whisper-api'
  preferredMethod: 'browser',

  // Auto-fallback if browser API fails
  autoFallback: true,

  // Cleanup configuration
  cleanupMethod: 'basic', // 'basic', 'claude', 'openai', 'languagetool'
  claudeApiKey: null,
  openaiApiKey: null,

  // Language
  language: 'en-US',

  // Continuous mode (keeps listening)
  continuous: true,

  // Show interim results
  interimResults: true
};

/**
 * Initialize the STT library with configuration
 * @param {Object} options - Configuration options
 */
export function init(options = {}) {
  config = { ...config, ...options };
}

/**
 * Start speech-to-text transcription
 * @param {Object} options - Override configuration for this session
 * @returns {Promise<string>} Transcribed text
 */
export async function startSpeechToText(options = {}) {
  const sessionConfig = { ...config, ...options };

  try {
    // Try browser API first (if preferred or available)
    if (sessionConfig.preferredMethod === 'browser' && isBrowserAPIAvailable()) {
      console.log('Using Browser Speech API');
      return await browserSTT(sessionConfig);
    }

    // Fallback to Whisper API
    if (sessionConfig.whisperApiKey) {
      console.log('Using Whisper API');
      return await whisperAPI(sessionConfig);
    }

    throw new Error('No STT method available. Configure API keys or use browser with Speech API support.');

  } catch (error) {
    console.error('STT Error:', error);

    // Auto-fallback logic
    if (sessionConfig.autoFallback) {
      if (sessionConfig.preferredMethod === 'browser' && sessionConfig.whisperApiKey) {
        console.log('Browser API failed, falling back to Whisper API');
        return await whisperAPI(sessionConfig);
      }
    }

    throw error;
  }
}

/**
 * Record audio and transcribe (for manual control)
 * @param {number} duration - Recording duration in seconds (optional)
 * @returns {Promise<string>} Transcribed text
 */
export async function recordAndTranscribe(duration = null) {
  return new Promise((resolve, reject) => {
    if (!isBrowserAPIAvailable()) {
      reject(new Error('Browser Speech API not available'));
      return;
    }

    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = config.language;

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      resolve(transcript);
    };

    recognition.onerror = (event) => {
      reject(new Error(`Speech recognition error: ${event.error}`));
    };

    recognition.start();

    // Auto-stop after duration
    if (duration) {
      setTimeout(() => {
        recognition.stop();
      }, duration * 1000);
    }
  });
}

/**
 * Clean up transcribed text (add punctuation, fix grammar, etc.)
 * @param {string} text - Raw transcribed text
 * @param {Object} options - Cleanup options
 * @returns {Promise<string>} Cleaned text
 */
export async function cleanup(text, options = {}) {
  const cleanupOptions = { ...config, ...options };
  return await cleanupText(text, cleanupOptions);
}

/**
 * Check if Browser Speech API is available
 * @returns {boolean}
 */
export function isBrowserAPIAvailable() {
  return typeof window !== 'undefined' &&
         (window.SpeechRecognition || window.webkitSpeechRecognition);
}

/**
 * Get current configuration
 * @returns {Object}
 */
export function getConfig() {
  return { ...config };
}

// Export individual modules for advanced usage
export { browserSTT } from './browser-stt';
export { whisperAPI } from './whisper-api';
export { cleanupText } from './grammar-cleanup';
