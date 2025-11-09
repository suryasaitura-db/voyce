#!/usr/bin/env python3
"""
Simple icon generator for Voyce Chrome Extension
Creates placeholder icons with gradient background and microphone symbol
Requires: PIL/Pillow (pip install Pillow)
"""

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow not installed. Install with: pip install Pillow")
    exit(1)

def create_icon(size):
    """Create a gradient icon with white circle"""
    # Create image
    img = Image.new('RGB', (size, size))
    draw = ImageDraw.Draw(img)

    # Draw gradient background (purple to blue)
    for y in range(size):
        # Interpolate between colors
        r = int(102 + (118 - 102) * y / size)
        g = int(126 + (75 - 126) * y / size)
        b = int(234 + (162 - 234) * y / size)
        draw.line([(0, y), (size, y)], fill=(r, g, b))

    # Draw white circle in center
    center = size // 2
    radius = size // 3
    draw.ellipse(
        [center - radius, center - radius, center + radius, center + radius],
        fill='white'
    )

    # Draw microphone shape (simplified)
    mic_height = size // 4
    mic_width = size // 6
    mic_x = center - mic_width // 2
    mic_y = center - mic_height // 2

    # Mic body (rounded rectangle approximation)
    draw.ellipse(
        [mic_x, mic_y, mic_x + mic_width, mic_y + mic_height],
        fill=(102, 126, 234)
    )

    # Save
    filename = f'icon{size}.png'
    img.save(filename, 'PNG')
    print(f'Created {filename}')

# Generate all three sizes
for size in [16, 48, 128]:
    create_icon(size)

print('\nIcons created successfully!')
print('You can now load the extension in Chrome.')
