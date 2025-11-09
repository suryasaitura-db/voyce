// DOM Elements
const recordButton = document.getElementById('recordButton');
const recordButtonText = recordButton.querySelector('.text');
const timer = document.getElementById('timer');
const statusMessage = document.getElementById('statusMessage');
const queueCounter = document.getElementById('queueCounter');
const languageSelect = document.getElementById('languageSelect');
const categorySelect = document.getElementById('categorySelect');
const authTokenInput = document.getElementById('authToken');
const saveTokenButton = document.getElementById('saveToken');
const uploadQueueButton = document.getElementById('uploadQueueButton');
const clearQueueButton = document.getElementById('clearQueueButton');
const recordingIndicator = document.getElementById('recordingIndicator');
const connectionStatus = document.getElementById('connectionStatus');
const connectionText = document.getElementById('connectionText');

// State
let mediaRecorder = null;
let audioChunks = [];
let recordingStartTime = null;
let timerInterval = null;
let isRecording = false;
let recordingQueue = [];

// Constants
const API_ENDPOINT = 'https://api.yourapp.com/v1/voice/upload';
const MAX_RECORDING_TIME = 300; // 5 minutes in seconds

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  loadAuthToken();
  loadQueue();
  updateQueueCounter();
  checkOnlineStatus();
  setInterval(checkOnlineStatus, 5000); // Check every 5 seconds
});

// Load saved auth token
async function loadAuthToken() {
  const result = await chrome.storage.local.get(['authToken']);
  if (result.authToken) {
    authTokenInput.value = result.authToken;
  }
}

// Save auth token
saveTokenButton.addEventListener('click', async () => {
  const token = authTokenInput.value.trim();
  await chrome.storage.local.set({ authToken: token });
  updateStatus(token ? 'Token saved successfully' : 'Token cleared', 'success');
});

// Load queue from storage
async function loadQueue() {
  const result = await chrome.storage.local.get(['recordingQueue']);
  recordingQueue = result.recordingQueue || [];
  updateQueueCounter();
  updateQueueButtons();
}

// Update queue counter
function updateQueueCounter() {
  queueCounter.textContent = `Queue: ${recordingQueue.length}`;
}

// Update queue action buttons
function updateQueueButtons() {
  const hasItems = recordingQueue.length > 0;
  uploadQueueButton.disabled = !hasItems;
  clearQueueButton.disabled = !hasItems;
}

// Check online status
function checkOnlineStatus() {
  const isOnline = navigator.onLine;
  connectionStatus.className = `status-dot ${isOnline ? 'online' : 'offline'}`;
  connectionText.textContent = isOnline ? 'Online' : 'Offline';

  // Auto-upload queue when coming online
  if (isOnline && recordingQueue.length > 0) {
    setTimeout(() => {
      if (confirm(`You're online! Upload ${recordingQueue.length} queued recording(s)?`)) {
        uploadQueue();
      }
    }, 1000);
  }
}

// Update status message
function updateStatus(message, type = 'info') {
  statusMessage.textContent = message;
  statusMessage.style.color = type === 'error' ? '#e53e3e' : type === 'success' ? '#48bb78' : '#555';
}

// Format time
function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

// Start timer
function startTimer() {
  recordingStartTime = Date.now();
  timerInterval = setInterval(() => {
    const elapsed = Math.floor((Date.now() - recordingStartTime) / 1000);
    timer.textContent = formatTime(elapsed);

    // Auto-stop at max recording time
    if (elapsed >= MAX_RECORDING_TIME) {
      stopRecording();
      updateStatus('Maximum recording time reached', 'info');
    }
  }, 1000);
}

// Stop timer
function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
  timer.textContent = '00:00';
}

// Request microphone permission and start recording
async function startRecording() {
  try {
    updateStatus('Requesting microphone access...', 'info');

    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        sampleRate: 44100
      }
    });

    // Determine the best audio format
    const mimeType = getSupportedMimeType();

    mediaRecorder = new MediaRecorder(stream, {
      mimeType: mimeType,
      audioBitsPerSecond: 128000
    });

    audioChunks = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
      }
    };

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: mimeType });
      await saveRecording(audioBlob);

      // Stop all tracks
      stream.getTracks().forEach(track => track.stop());
    };

    mediaRecorder.start();
    isRecording = true;

    // Update UI
    recordButton.classList.add('recording');
    recordButtonText.textContent = 'Stop Recording';
    recordingIndicator.classList.add('active');
    startTimer();
    updateStatus('Recording...', 'info');

    // Disable controls during recording
    languageSelect.disabled = true;
    categorySelect.disabled = true;

  } catch (error) {
    console.error('Error starting recording:', error);
    updateStatus('Microphone access denied or not available', 'error');
    isRecording = false;
  }
}

// Get supported MIME type
function getSupportedMimeType() {
  const types = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/mp4',
    'audio/mpeg'
  ];

  for (const type of types) {
    if (MediaRecorder.isTypeSupported(type)) {
      return type;
    }
  }

  return 'audio/webm'; // fallback
}

// Stop recording
function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
    isRecording = false;

    // Update UI
    recordButton.classList.remove('recording');
    recordButtonText.textContent = 'Start Recording';
    recordingIndicator.classList.remove('active');
    stopTimer();

    // Re-enable controls
    languageSelect.disabled = false;
    categorySelect.disabled = false;

    updateStatus('Processing recording...', 'info');
  }
}

// Save recording to queue
async function saveRecording(audioBlob) {
  const recording = {
    id: Date.now().toString(),
    timestamp: new Date().toISOString(),
    language: languageSelect.value,
    category: categorySelect.value,
    audioData: await blobToBase64(audioBlob),
    mimeType: audioBlob.type,
    size: audioBlob.size,
    duration: Math.floor((Date.now() - recordingStartTime) / 1000)
  };

  recordingQueue.push(recording);
  await chrome.storage.local.set({ recordingQueue });

  updateQueueCounter();
  updateQueueButtons();
  updateStatus(`Recording saved to queue (${formatFileSize(audioBlob.size)})`, 'success');

  // Try to upload immediately if online
  if (navigator.onLine) {
    uploadQueue();
  } else {
    updateStatus('Offline - Recording saved to queue', 'info');
  }
}

// Convert blob to base64
function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

// Convert base64 to blob
function base64ToBlob(base64, mimeType) {
  const byteString = atob(base64.split(',')[1]);
  const ab = new ArrayBuffer(byteString.length);
  const ia = new Uint8Array(ab);

  for (let i = 0; i < byteString.length; i++) {
    ia[i] = byteString.charCodeAt(i);
  }

  return new Blob([ab], { type: mimeType });
}

// Format file size
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

// Upload queue to server
async function uploadQueue() {
  if (recordingQueue.length === 0) {
    updateStatus('Queue is empty', 'info');
    return;
  }

  if (!navigator.onLine) {
    updateStatus('Cannot upload - you are offline', 'error');
    return;
  }

  updateStatus(`Uploading ${recordingQueue.length} recording(s)...`, 'info');
  uploadQueueButton.disabled = true;

  let successCount = 0;
  let failCount = 0;
  const failedRecordings = [];

  // Upload each recording
  for (const recording of recordingQueue) {
    try {
      await uploadRecording(recording);
      successCount++;
    } catch (error) {
      console.error('Upload failed:', error);
      failCount++;
      failedRecordings.push(recording);
    }
  }

  // Update queue with only failed recordings
  recordingQueue = failedRecordings;
  await chrome.storage.local.set({ recordingQueue });

  updateQueueCounter();
  updateQueueButtons();

  if (failCount === 0) {
    updateStatus(`Successfully uploaded ${successCount} recording(s)`, 'success');
  } else {
    updateStatus(`Uploaded ${successCount}, failed ${failCount}`, 'error');
  }
}

// Upload single recording
async function uploadRecording(recording) {
  const result = await chrome.storage.local.get(['authToken']);
  const token = result.authToken || '';

  // Convert base64 to blob
  const audioBlob = base64ToBlob(recording.audioData, recording.mimeType);

  // Create FormData
  const formData = new FormData();
  formData.append('audio', audioBlob, `recording_${recording.id}.webm`);
  formData.append('language', recording.language);
  formData.append('category', recording.category);
  formData.append('timestamp', recording.timestamp);
  formData.append('duration', recording.duration.toString());

  // Upload
  const headers = {
    'Accept': 'application/json'
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(API_ENDPOINT, {
    method: 'POST',
    headers: headers,
    body: formData
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Upload failed: ${response.status} - ${errorText}`);
  }

  return await response.json();
}

// Clear queue
clearQueueButton.addEventListener('click', async () => {
  if (confirm(`Clear ${recordingQueue.length} recording(s) from queue?`)) {
    recordingQueue = [];
    await chrome.storage.local.set({ recordingQueue });
    updateQueueCounter();
    updateQueueButtons();
    updateStatus('Queue cleared', 'success');
  }
});

// Upload queue button
uploadQueueButton.addEventListener('click', () => {
  uploadQueue();
});

// Record button toggle
recordButton.addEventListener('click', () => {
  if (isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  // Space or R to toggle recording
  if ((e.code === 'Space' || e.code === 'KeyR') && !e.target.matches('input, select')) {
    e.preventDefault();
    recordButton.click();
  }

  // Escape to stop recording
  if (e.code === 'Escape' && isRecording) {
    e.preventDefault();
    stopRecording();
  }
});

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'UPLOAD_COMPLETE') {
    loadQueue();
    updateStatus('Background upload completed', 'success');
  } else if (message.type === 'UPLOAD_FAILED') {
    updateStatus('Background upload failed', 'error');
  }
});
