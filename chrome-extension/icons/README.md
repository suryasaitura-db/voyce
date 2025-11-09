# Icons Placeholder

This directory should contain the following icon files for the Voyce Chrome Extension:

- `icon16.png` - 16x16 pixels (toolbar icon)
- `icon48.png` - 48x48 pixels (extension management page)
- `icon128.png` - 128x128 pixels (Chrome Web Store)

## Creating Icons

You can create icons using any design tool. Here are the recommended specifications:

### Design Guidelines
- **Colors**: Use the brand gradient (purple to blue: #667eea to #764ba2)
- **Symbol**: Microphone or voice wave icon
- **Style**: Modern, clean, minimal
- **Background**: Transparent or solid color

### Quick Generation Options

1. **Using Online Tools**:
   - [Favicon.io](https://favicon.io) - Generate from text or image
   - [RealFaviconGenerator](https://realfavicongenerator.net) - Comprehensive icon generator

2. **Using Design Tools**:
   - Figma, Sketch, or Adobe Illustrator
   - Export at 16x16, 48x48, and 128x128 pixels
   - Save as PNG with transparency

3. **Using Code**:
   ```bash
   # If you have ImageMagick installed:
   convert -size 128x128 -background "#667eea" -fill white -gravity center -font Arial-Bold -pointsize 80 label:"V" icon128.png
   convert icon128.png -resize 48x48 icon48.png
   convert icon128.png -resize 16x16 icon16.png
   ```

## Temporary Testing

For testing purposes, you can use placeholder colored squares:

1. Create simple colored PNG files with the required dimensions
2. Or download free icon sets from:
   - [Icons8](https://icons8.com/icons/set/microphone)
   - [Flaticon](https://www.flaticon.com/search?word=microphone)

**Note**: Replace these placeholders with proper branded icons before publishing to Chrome Web Store.
