/**
 * OpenAI Whisper API implementation
 * PAID - $0.006 per minute
 */

import axios from 'axios';

export async function whisperAPI(config) {
  if (!config.whisperApiKey) {
    throw new Error('Whisper API key required');
  }

  // Record audio from microphone
  const audioBlob = await recordAudio(config.duration || 30);

  // Send to Whisper API
  const transcript = await transcribeWithWhisper(audioBlob, config);

  return transcript;
}

/**
 * Record audio from microphone
 */
async function recordAudio(maxDuration = 30) {
  return new Promise(async (resolve, reject) => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const audioChunks = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        stream.getTracks().forEach(track => track.stop());
        resolve(audioBlob);
      };

      mediaRecorder.onerror = (error) => {
        stream.getTracks().forEach(track => track.stop());
        reject(error);
      };

      // Start recording
      mediaRecorder.start();

      // Auto-stop after max duration
      setTimeout(() => {
        if (mediaRecorder.state === 'recording') {
          mediaRecorder.stop();
        }
      }, maxDuration * 1000);

      // Allow manual stop via config callback
      if (config.onStart) {
        config.onStart({
          stop: () => mediaRecorder.stop(),
          isRecording: () => mediaRecorder.state === 'recording'
        });
      }

    } catch (error) {
      reject(error);
    }
  });
}

/**
 * Transcribe audio using OpenAI Whisper API
 */
async function transcribeWithWhisper(audioBlob, config) {
  const formData = new FormData();
  formData.append('file', audioBlob, 'audio.webm');
  formData.append('model', 'whisper-1');

  if (config.language && config.language !== 'auto') {
    // Convert language code to Whisper format (e.g., 'en-US' -> 'en')
    const lang = config.language.split('-')[0];
    formData.append('language', lang);
  }

  try {
    const response = await axios.post(
      'https://api.openai.com/v1/audio/transcriptions',
      formData,
      {
        headers: {
          'Authorization': `Bearer ${config.whisperApiKey}`,
          'Content-Type': 'multipart/form-data'
        }
      }
    );

    return response.data.text;

  } catch (error) {
    console.error('Whisper API error:', error.response?.data || error.message);
    throw new Error(`Whisper API transcription failed: ${error.message}`);
  }
}

/**
 * Manual recording control for Whisper API
 * Gives user full control over start/stop
 */
export function createWhisperRecorder(config) {
  let mediaRecorder = null;
  let stream = null;
  let audioChunks = [];

  return {
    start: async () => {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      mediaRecorder.start();
    },

    stop: async () => {
      return new Promise((resolve, reject) => {
        if (!mediaRecorder) {
          reject(new Error('Recording not started'));
          return;
        }

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
          stream.getTracks().forEach(track => track.stop());

          try {
            const transcript = await transcribeWithWhisper(audioBlob, config);
            resolve(transcript);
          } catch (error) {
            reject(error);
          }
        };

        mediaRecorder.stop();
      });
    },

    isRecording: () => mediaRecorder && mediaRecorder.state === 'recording'
  };
}
