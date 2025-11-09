// Background Service Worker for Voyce Chrome Extension
// Handles background uploads, sync, and notifications

const API_ENDPOINT = 'https://api.yourapp.com/v1/voice/upload';
const SYNC_INTERVAL = 15; // minutes

// Install event
chrome.runtime.onInstalled.addListener((details) => {
  console.log('Voyce extension installed/updated', details.reason);

  // Set up periodic sync alarm
  chrome.alarms.create('syncQueue', {
    periodInMinutes: SYNC_INTERVAL
  });

  // Show welcome notification
  if (details.reason === 'install') {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: '../icons/icon128.png',
      title: 'Voyce Installed',
      message: 'Voice feedback platform is ready to use. Click the extension icon to start recording.',
      priority: 2
    });
  }
});

// Alarm listener for periodic sync
chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === 'syncQueue') {
    console.log('Periodic sync triggered');
    await syncQueue();
  }
});

// Message listener from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'UPLOAD_QUEUE') {
    syncQueue().then((result) => {
      sendResponse(result);
    });
    return true; // Keep channel open for async response
  }
});

// Sync queue - upload pending recordings
async function syncQueue() {
  // Check if online
  if (!navigator.onLine) {
    console.log('Offline - skipping sync');
    return { success: false, reason: 'offline' };
  }

  // Get queue from storage
  const result = await chrome.storage.local.get(['recordingQueue', 'authToken']);
  const queue = result.recordingQueue || [];
  const token = result.authToken || '';

  if (queue.length === 0) {
    console.log('Queue is empty');
    return { success: true, uploaded: 0 };
  }

  console.log(`Syncing ${queue.length} recordings...`);

  let successCount = 0;
  let failCount = 0;
  const failedRecordings = [];

  // Upload each recording
  for (const recording of queue) {
    try {
      await uploadRecording(recording, token);
      successCount++;
      console.log(`Uploaded recording ${recording.id}`);
    } catch (error) {
      console.error(`Failed to upload recording ${recording.id}:`, error);
      failCount++;
      failedRecordings.push(recording);
    }
  }

  // Update queue with only failed recordings
  await chrome.storage.local.set({ recordingQueue: failedRecordings });

  // Show notification if any uploads succeeded
  if (successCount > 0) {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: '../icons/icon128.png',
      title: 'Voyce Upload Complete',
      message: `Successfully uploaded ${successCount} recording(s)${failCount > 0 ? `, ${failCount} failed` : ''}`,
      priority: 1
    });

    // Send message to popup if it's open
    try {
      chrome.runtime.sendMessage({
        type: 'UPLOAD_COMPLETE',
        successCount,
        failCount
      });
    } catch (e) {
      // Popup might not be open, ignore
    }
  }

  return {
    success: failCount === 0,
    uploaded: successCount,
    failed: failCount
  };
}

// Upload single recording to API
async function uploadRecording(recording, token) {
  // Convert base64 to blob
  const audioBlob = base64ToBlob(recording.audioData, recording.mimeType);

  // Create FormData
  const formData = new FormData();
  formData.append('audio', audioBlob, `recording_${recording.id}.webm`);
  formData.append('language', recording.language);
  formData.append('category', recording.category);
  formData.append('timestamp', recording.timestamp);
  formData.append('duration', recording.duration.toString());

  // Set headers
  const headers = {
    'Accept': 'application/json'
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Upload
  const response = await fetch(API_ENDPOINT, {
    method: 'POST',
    headers: headers,
    body: formData
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }

  const data = await response.json();
  return data;
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

// Listen for online/offline events
self.addEventListener('online', async () => {
  console.log('Connection restored - syncing queue');
  const result = await syncQueue();

  if (result.uploaded > 0) {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: '../icons/icon128.png',
      title: 'Voyce - Back Online',
      message: `Uploaded ${result.uploaded} queued recording(s)`,
      priority: 1
    });
  }
});

self.addEventListener('offline', () => {
  console.log('Connection lost - recordings will be queued');
});

// Handle notification clicks
chrome.notifications.onClicked.addListener((notificationId) => {
  // Open popup when notification is clicked
  chrome.action.openPopup();
});

// Export functions for testing (if needed)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    syncQueue,
    uploadRecording,
    base64ToBlob
  };
}
