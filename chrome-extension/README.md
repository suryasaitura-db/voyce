# Voyce - Voice Feedback Chrome Extension

A Chrome Extension (Manifest V3) for recording and submitting voice feedback in multiple languages. Supports offline recording with automatic sync when connection is restored.

## Features

- **Voice Recording**: Record audio feedback using the MediaRecorder API
- **Multi-language Support**: English, Spanish, Hindi, Tamil, Telugu, Kannada, Malayalam
- **Category Selection**: Government, Private, Product, Infrastructure, Health
- **Offline Queue**: Recordings are saved locally when offline and auto-uploaded when online
- **JWT Authentication**: Optional token-based authentication
- **Clean UI**: Modern, gradient-based design with recording timer
- **Background Sync**: Automatic periodic upload of queued recordings
- **Notifications**: Status updates for uploads and sync events
- **Keyboard Shortcuts**: Space/R to record, Escape to stop

## Installation

### For Development/Testing

1. **Clone or download this extension folder**
   ```bash
   cd /Users/suryasai.turaga/voyce/chrome-extension
   ```

2. **Create icon files** (required before loading)
   - Navigate to the `icons/` folder
   - Create three PNG files: `icon16.png`, `icon48.png`, `icon128.png`
   - See `icons/README.md` for details and quick generation methods
   - For quick testing, you can use any placeholder images with those dimensions

3. **Open Chrome and navigate to Extensions**
   ```
   chrome://extensions/
   ```

4. **Enable Developer Mode**
   - Toggle the "Developer mode" switch in the top-right corner

5. **Load the extension**
   - Click "Load unpacked"
   - Select the `/Users/suryasai.turaga/voyce/chrome-extension/` directory
   - The extension should now appear in your extensions list

6. **Pin the extension** (optional)
   - Click the puzzle icon in Chrome toolbar
   - Find "Voyce - Voice Feedback Platform"
   - Click the pin icon to keep it visible in the toolbar

## Usage

### Recording Voice Feedback

1. **Click the extension icon** in the Chrome toolbar
2. **Select language** from the dropdown (default: English)
3. **Select category** (Government, Private, Product, Infrastructure, Health)
4. **Click the record button** or press Space/R
5. **Speak your feedback** (maximum 5 minutes)
6. **Click stop** or press Escape to finish recording
7. Recording is automatically saved to queue and uploaded if online

### Authentication (Optional)

1. Enter your JWT token in the "Authentication Token" field
2. Click "Save Token" to store it
3. The token will be included in all API requests

### Managing Queue

- **Queue Counter**: Shows number of pending uploads
- **Upload Queue**: Manually trigger upload of all queued recordings
- **Clear Queue**: Remove all queued recordings (with confirmation)

### Offline Mode

- Recordings made while offline are saved to local storage
- When connection is restored, you'll be prompted to upload queued items
- Background sync runs every 15 minutes to auto-upload pending recordings

## Configuration

### API Endpoint

The default API endpoint is: `https://api.yourapp.com/v1/voice/upload`

To change it:
1. Edit `popup/popup.js` and `background/background.js`
2. Update the `API_ENDPOINT` constant
3. Reload the extension

### Supported Audio Formats

The extension automatically detects and uses the best supported format:
- `audio/webm;codecs=opus` (preferred)
- `audio/webm`
- `audio/ogg;codecs=opus`
- `audio/mp4`
- `audio/mpeg`

## API Integration

### Upload Endpoint

**POST** `https://api.yourapp.com/v1/voice/upload`

**Headers**:
```
Content-Type: multipart/form-data
Authorization: Bearer <JWT_TOKEN> (optional)
Accept: application/json
```

**Form Data**:
```
audio: <audio file> (WebM/OGG/MP3)
language: <language_code> (en, es, hi, ta, te, kn, ml)
category: <category> (government, private, product, infrastructure, health)
timestamp: <ISO 8601 timestamp>
duration: <seconds>
```

**Response**:
```json
{
  "success": true,
  "id": "recording_id",
  "message": "Recording uploaded successfully"
}
```

## File Structure

```
chrome-extension/
├── manifest.json           # Extension manifest (V3)
├── popup/
│   ├── popup.html         # Extension popup UI
│   ├── popup.css          # Styling with gradient theme
│   └── popup.js           # Recording logic and UI handlers
├── background/
│   └── background.js      # Service worker for background tasks
├── icons/
│   ├── icon16.png         # 16x16 toolbar icon
│   ├── icon48.png         # 48x48 extension management icon
│   ├── icon128.png        # 128x128 Chrome Web Store icon
│   └── README.md          # Icon creation guide
└── README.md              # This file
```

## Permissions

The extension requires the following permissions:

- **storage**: Save recordings and settings locally
- **notifications**: Show upload status notifications
- **alarms**: Periodic background sync
- **host_permissions**: Access to API endpoint for uploads

## Development

### Testing

1. **Test recording**: Click record and speak
2. **Test offline mode**: Disconnect internet, record, then reconnect
3. **Test queue**: Record multiple items offline, then upload
4. **Test authentication**: Add a valid JWT token and verify it's sent in requests

### Debugging

1. **Popup console**:
   - Right-click extension icon → "Inspect popup"
   - View console logs and debug UI issues

2. **Background service worker**:
   - Go to `chrome://extensions/`
   - Find Voyce extension
   - Click "service worker" link
   - View background task logs

3. **Storage inspection**:
   - In popup console: `chrome.storage.local.get(null, console.log)`
   - Or use Chrome DevTools → Application → Storage → Extension Storage

### Common Issues

**Issue**: Microphone access denied
- **Solution**: Check Chrome settings → Privacy and Security → Site Settings → Microphone

**Issue**: Icons not showing
- **Solution**: Create the required PNG files in the `icons/` folder (see icons/README.md)

**Issue**: Upload fails with CORS error
- **Solution**: Ensure API endpoint has proper CORS headers or add the domain to `host_permissions` in manifest.json

**Issue**: Extension won't load
- **Solution**: Check for syntax errors in console, ensure all files are present

## Publishing to Chrome Web Store

1. Create proper branded icons (replace placeholders)
2. Test thoroughly on different systems
3. Create promotional images and screenshots
4. Prepare privacy policy (if collecting user data)
5. Visit [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/developer/dashboard)
6. Pay one-time $5 developer fee
7. Upload extension ZIP file
8. Fill in store listing details
9. Submit for review

## Security Considerations

- JWT tokens are stored in `chrome.storage.local` (not synced across devices)
- Audio data is temporarily stored as base64 in local storage
- All API communication uses HTTPS
- No analytics or tracking included
- Microphone permission requested only when recording

## Browser Compatibility

- **Chrome**: Version 88+ (Manifest V3 support)
- **Edge**: Version 88+ (Chromium-based)
- **Opera**: Version 74+
- **Brave**: Latest version

**Note**: Firefox uses different extension format (WebExtensions) and would require modifications.

## License

This extension is part of the Voyce voice feedback platform.

## Support

For issues or questions:
1. Check this README
2. Review console logs for errors
3. Verify API endpoint is accessible
4. Test with placeholder icons first

## Roadmap

Future enhancements:
- [ ] Audio visualization during recording
- [ ] Playback before upload
- [ ] Edit/delete queued recordings
- [ ] Upload progress indicator
- [ ] Multiple language UI translations
- [ ] Voice activity detection
- [ ] Recording compression
- [ ] Cloud sync for queue across devices
- [ ] Analytics dashboard link

---

**Version**: 1.0.0
**Last Updated**: 2025-11-08
**Manifest Version**: 3
