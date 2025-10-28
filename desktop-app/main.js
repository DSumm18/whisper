const { app, BrowserWindow, Tray, Menu, globalShortcut, ipcMain } = require('electron');
const path = require('path');
const axios = require('axios');
const robot = require('node-key-sender');

let mainWindow;
let tray;
let isRecording = false;
const WHISPER_SERVICE_URL = 'http://localhost:5000';

// Create the always-on bottom window
function createWindow() {
  const { screen } = require('electron');
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.workAreaSize;

  mainWindow = new BrowserWindow({
    width: 400,
    height: 80,
    x: width / 2 - 200,
    y: height - 100,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  mainWindow.loadFile('renderer/index.html');

  // Hide initially
  mainWindow.hide();

  // Prevent window from being closed, just hide it
  mainWindow.on('close', (event) => {
    if (!app.isQuitting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });
}

// Create system tray icon
function createTray() {
  // Create a simple colored icon (you can replace with actual icon file)
  tray = new Tray(path.join(__dirname, 'icon.png'));

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show/Hide',
      click: () => {
        mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
      }
    },
    {
      label: 'Start Recording (Ctrl+Shift+V)',
      click: () => startRecording()
    },
    { type: 'separator' },
    {
      label: 'Settings',
      click: () => {
        // TODO: Open settings window
        console.log('Settings clicked');
      }
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        app.isQuitting = true;
        app.quit();
      }
    }
  ]);

  tray.setToolTip('Whisper Voice Typing');
  tray.setContextMenu(contextMenu);

  // Click to toggle window
  tray.on('click', () => {
    mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
  });
}

// Register global shortcuts
function registerShortcuts() {
  // Ctrl+Shift+V to start/stop recording
  const ret = globalShortcut.register('CommandOrControl+Shift+V', () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  });

  if (!ret) {
    console.log('Registration failed');
  }
}

// Start recording audio
async function startRecording() {
  isRecording = true;
  mainWindow.show();
  mainWindow.webContents.send('recording-started');

  try {
    // Start recording via Python backend
    const response = await axios.post(`${WHISPER_SERVICE_URL}/start-recording`);
    console.log('Recording started:', response.data);
  } catch (error) {
    console.error('Failed to start recording:', error.message);
    mainWindow.webContents.send('error', 'Failed to connect to Whisper service. Make sure it\'s running!');
    isRecording = false;
  }
}

// Stop recording and get transcription
async function stopRecording() {
  isRecording = false;
  mainWindow.webContents.send('recording-stopped');
  mainWindow.webContents.send('processing');

  try {
    // Get transcription from Python backend
    const response = await axios.post(`${WHISPER_SERVICE_URL}/stop-recording`);
    const { transcript, cleaned_text } = response.data;

    console.log('Transcript:', transcript);
    console.log('Cleaned:', cleaned_text);

    // Send to renderer for display
    mainWindow.webContents.send('transcription-ready', cleaned_text);

    // Type the text
    await typeText(cleaned_text);

    // Hide window after typing
    setTimeout(() => {
      mainWindow.hide();
    }, 2000);

  } catch (error) {
    console.error('Failed to get transcription:', error.message);
    mainWindow.webContents.send('error', 'Transcription failed!');
  }
}

// Type text using keyboard simulation
async function typeText(text) {
  try {
    // Wait a moment for user to focus the target application
    await new Promise(resolve => setTimeout(resolve, 500));

    // Type the text
    await robot.sendText(text);
  } catch (error) {
    console.error('Failed to type text:', error);
  }
}

// IPC handlers
ipcMain.on('toggle-recording', () => {
  if (isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
});

ipcMain.on('hide-window', () => {
  mainWindow.hide();
});

// App lifecycle
app.whenReady().then(() => {
  createWindow();
  createTray();
  registerShortcuts();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
});

// Check if Whisper service is running
async function checkWhisperService() {
  try {
    await axios.get(`${WHISPER_SERVICE_URL}/health`);
    console.log('Whisper service is running');
  } catch (error) {
    console.error('Whisper service not running. Please start it with: cd whisper-service && python whisper_server.py');
  }
}

// Check on startup
setTimeout(checkWhisperService, 2000);
