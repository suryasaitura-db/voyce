# Quick Icon Setup

You need three icon files to load the extension: `icon16.png`, `icon48.png`, and `icon128.png`

## Option 1: Download Free Icons (Fastest)

1. Visit [Icons8 Microphone](https://icons8.com/icons/set/microphone)
2. Download a microphone icon in PNG format
3. Download in sizes: 16px, 48px, and 128px
4. Rename files to `icon16.png`, `icon48.png`, `icon128.png`
5. Place in this `icons/` folder

## Option 2: Use Online Generator

1. Visit [Favicon.io](https://favicon.io/favicon-generator/)
2. Enter text: "V"
3. Choose purple/blue colors (#667eea)
4. Download the favicon package
5. Extract and rename the appropriate sizes

## Option 3: Create Simple Colored Squares (Quick Testing)

Use any image editor or online tool:
- Create 3 PNG files: 16x16, 48x48, 128x128 pixels
- Fill with solid color (#667eea - purple)
- Save as `icon16.png`, `icon48.png`, `icon128.png`

## Option 4: Use Python Script (Recommended)

If you have Python with Pillow:

```bash
pip install Pillow
python3 generate_icons.py
```

## Option 5: Use Node.js Script

If you have Node.js:

```bash
npm install canvas
node generate_icons.js
```

## Option 6: Manual Creation with Any Tool

Use Photoshop, GIMP, Figma, Sketch, or any image editor:

1. Create new image: 128x128 pixels
2. Fill with gradient (#667eea to #764ba2)
3. Add white circle or text "V" in center
4. Export as `icon128.png`
5. Resize to 48x48 → save as `icon48.png`
6. Resize to 16x16 → save as `icon16.png`

## Verify Icons

After creating icons, verify they exist:

```bash
ls -lh icon*.png
```

You should see:
- icon16.png
- icon48.png
- icon128.png

## Next Steps

Once icons are in place:
1. Open Chrome
2. Go to `chrome://extensions/`
3. Enable "Developer mode"
4. Click "Load unpacked"
5. Select the `/Users/suryasai.turaga/voyce/chrome-extension/` folder

Done! The extension should now be loaded.
