/**
 * Browser Web Speech API implementation
 * FREE - uses browser's built-in speech recognition
 */

export function browserSTT(config) {
  return new Promise((resolve, reject) => {
    // Check if API is available
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      reject(new Error('Browser Speech API not supported'));
      return;
    }

    const recognition = new SpeechRecognition();

    // Configure recognition
    recognition.continuous = config.continuous || false;
    recognition.interimResults = config.interimResults || false;
    recognition.lang = config.language || 'en-US';
    recognition.maxAlternatives = 1;

    let finalTranscript = '';
    let interimTranscript = '';

    // Handle results
    recognition.onresult = (event) => {
      interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;

        if (event.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interimTranscript += transcript;
        }
      }

      // Call interim callback if provided
      if (config.onInterim && interimTranscript) {
        config.onInterim(interimTranscript);
      }

      // Call partial callback if provided
      if (config.onPartial && finalTranscript) {
        config.onPartial(finalTranscript.trim());
      }
    };

    // Handle end
    recognition.onend = () => {
      resolve(finalTranscript.trim());
    };

    // Handle errors
    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);

      // Some errors are not critical
      if (event.error === 'no-speech') {
        reject(new Error('No speech detected'));
      } else if (event.error === 'audio-capture') {
        reject(new Error('No microphone access'));
      } else if (event.error === 'not-allowed') {
        reject(new Error('Microphone permission denied'));
      } else {
        reject(new Error(`Speech recognition error: ${event.error}`));
      }
    };

    // Start recognition
    try {
      recognition.start();

      // Store recognition instance for manual stop
      if (config.onStart) {
        config.onStart(recognition);
      }

    } catch (error) {
      reject(error);
    }
  });
}

/**
 * Create a continuous speech recognition session
 * Returns a controller object to start/stop/pause
 */
export function createContinuousSession(config = {}) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    throw new Error('Browser Speech API not supported');
  }

  const recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = config.language || 'en-US';

  let isActive = false;
  let finalTranscript = '';

  recognition.onresult = (event) => {
    let interimTranscript = '';

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;

      if (event.results[i].isFinal) {
        finalTranscript += transcript + ' ';
        if (config.onFinal) {
          config.onFinal(transcript);
        }
      } else {
        interimTranscript += transcript;
      }
    }

    if (config.onInterim && interimTranscript) {
      config.onInterim(interimTranscript);
    }
  };

  recognition.onerror = (event) => {
    if (config.onError) {
      config.onError(event.error);
    }
  };

  recognition.onend = () => {
    // Auto-restart if still active (for true continuous mode)
    if (isActive) {
      recognition.start();
    }
  };

  return {
    start: () => {
      isActive = true;
      finalTranscript = '';
      recognition.start();
    },

    stop: () => {
      isActive = false;
      recognition.stop();
      return finalTranscript.trim();
    },

    abort: () => {
      isActive = false;
      recognition.abort();
    },

    getTranscript: () => finalTranscript.trim(),

    isActive: () => isActive
  };
}
