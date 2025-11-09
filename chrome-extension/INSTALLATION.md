# Installation Checklist

Follow these steps to install and test the Voyce Chrome Extension.

## Prerequisites

- Google Chrome (version 88+), Microsoft Edge, or Brave Browser
- Microphone access
- Internet connection (for uploads)

## Step-by-Step Installation

### 1. Create Icon Files (Required)

The extension needs three icon files before it can be loaded. Choose one method:

**Quick Option** - Download from free icon sites:
- Visit https://icons8.com/icons/set/microphone
- Download PNG icons at 16px, 48px, and 128px
- Rename to `icon16.png`, `icon48.png`, `icon128.png`
- Place in `/Users/suryasai.turaga/voyce/chrome-extension/icons/`

**Or use a generator script**:
```bash
cd /Users/suryasai.turaga/voyce/chrome-extension/icons
# If you have Python + Pillow:
python3 generate_icons.py

# Or if you have Node.js + canvas:
npm install canvas
node generate_icons.js
```

See `icons/QUICKSTART.md` for more options.

### 2. Verify Files

Ensure these files exist:
```bash
cd /Users/suryasai.turaga/voyce/chrome-extension

# Check structure
ls -la
# Should see: manifest.json, README.md, popup/, background/, icons/

# Check icons
ls -la icons/
# Should see: icon16.png, icon48.png, icon128.png
```

### 3. Load Extension in Chrome

1. Open Google Chrome
2. Navigate to: `chrome://extensions/`
3. Toggle **Developer mode** (top-right corner)
4. Click **"Load unpacked"**
5. Select the folder: `/Users/suryasai.turaga/voyce/chrome-extension/`
6. Extension should appear in the list

### 4. Pin Extension (Optional)

1. Click the **puzzle icon** in Chrome toolbar (Extensions)
2. Find **"Voyce - Voice Feedback Platform"**
3. Click the **pin icon** to keep it visible

### 5. Configure API Endpoint (If Needed)

If your API endpoint is different from `https://api.yourapp.com/v1/voice/upload`:

1. Open `popup/popup.js`
2. Change line: `const API_ENDPOINT = 'https://api.yourapp.com/v1/voice/upload';`
3. Open `background/background.js`
4. Change line: `const API_ENDPOINT = 'https://api.yourapp.com/v1/voice/upload';`
5. Go to `chrome://extensions/`
6. Click the **reload icon** on the Voyce extension

## Testing the Extension

### Test 1: Basic Recording

1. Click the Voyce extension icon
2. Select language (e.g., English)
3. Select category (e.g., Government)
4. Click **"Start Recording"** button
5. Speak for a few seconds
6. Click **"Stop Recording"**
7. Verify: Status shows "Processing recording..."
8. Verify: Queue counter increases to "Queue: 1"

### Test 2: Offline Mode

1. Disconnect from internet (turn off WiFi)
2. Record another voice message
3. Verify: Status shows "Offline - Recording saved to queue"
4. Verify: Queue counter shows "Queue: 2"
5. Reconnect to internet
6. Verify: Popup asks to upload queued recordings

### Test 3: Authentication

1. Get a JWT token from your backend
2. Paste into "Authentication Token" field
3. Click **"Save Token"**
4. Record and upload a message
5. Verify token is sent in Authorization header (check Network tab)

### Test 4: Queue Management

1. Record 2-3 messages while offline
2. Click **"Upload Queue"** button
3. Verify: Successful upload message appears
4. Verify: Queue counter resets to 0
5. Test **"Clear Queue"** with new recordings

### Test 5: Keyboard Shortcuts

1. Open extension popup
2. Press **Space** or **R** - Should start recording
3. Press **Escape** - Should stop recording

## Debugging

### View Popup Console

1. Right-click the extension icon
2. Select **"Inspect popup"**
3. View console for errors/logs

### View Background Service Worker

1. Go to `chrome://extensions/`
2. Find Voyce extension
3. Click **"service worker"** link (under "Inspect views")
4. View background logs

### View Storage

1. Open popup console (right-click icon → Inspect)
2. Go to **Application** tab
3. Navigate to **Storage** → **Extension Storage**
4. View `recordingQueue` and `authToken`

Or in console:
```javascript
chrome.storage.local.get(null, console.log)
```

### Common Issues

**Problem**: Extension won't load
- **Solution**: Ensure all files are present, especially manifest.json and icons

**Problem**: Microphone not working
- **Solution**: Check Chrome settings → Privacy → Microphone permissions

**Problem**: Icons not showing
- **Solution**: Create the three PNG files in icons/ folder (see Step 1)

**Problem**: Upload fails
- **Solution**: Check API endpoint URL, verify CORS headers on server

**Problem**: CORS errors
- **Solution**: Add your API domain to `host_permissions` in manifest.json

## Permissions Explained

The extension requests these permissions:

- **storage**: Save recordings and settings locally when offline
- **notifications**: Show upload status and sync notifications
- **alarms**: Schedule periodic background sync (every 15 minutes)
- **host_permissions** (api.yourapp.com): Upload recordings to your server

## Next Steps

- Customize the API endpoint for your backend
- Add your branding to icons
- Configure server to accept uploads
- Test end-to-end workflow
- Prepare for Chrome Web Store submission (optional)

## File Locations

- **Extension root**: `/Users/suryasai.turaga/voyce/chrome-extension/`
- **Manifest**: `/Users/suryasai.turaga/voyce/chrome-extension/manifest.json`
- **Popup UI**: `/Users/suryasai.turaga/voyce/chrome-extension/popup/`
- **Background**: `/Users/suryasai.turaga/voyce/chrome-extension/background/`
- **Icons**: `/Users/suryasai.turaga/voyce/chrome-extension/icons/`

## Support Resources

- [Chrome Extension Documentation](https://developer.chrome.com/docs/extensions/)
- [MediaRecorder API](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder)
- [Manifest V3 Migration](https://developer.chrome.com/docs/extensions/mv3/intro/)

---

**Ready to go!** Once icons are created, you can load the extension and start testing.
