#!/usr/bin/env node
/**
 * Simple icon generator using Canvas
 * Run with: node generate_icons.js
 * Requires: npm install canvas
 */

const fs = require('fs');

try {
  const { createCanvas } = require('canvas');

  function createIcon(size) {
    const canvas = createCanvas(size, size);
    const ctx = canvas.getContext('2d');

    // Create gradient background
    const gradient = ctx.createLinearGradient(0, 0, size, size);
    gradient.addColorStop(0, '#667eea');
    gradient.addColorStop(1, '#764ba2');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, size, size);

    // Draw white circle (microphone base)
    ctx.fillStyle = 'white';
    ctx.beginPath();
    ctx.arc(size / 2, size / 2, size / 3, 0, Math.PI * 2);
    ctx.fill();

    // Draw simple microphone icon
    ctx.fillStyle = '#667eea';
    const micWidth = size / 6;
    const micHeight = size / 4;
    const x = (size - micWidth) / 2;
    const y = (size - micHeight) / 2;

    // Mic capsule
    ctx.beginPath();
    ctx.roundRect(x, y, micWidth, micHeight, micWidth / 2);
    ctx.fill();

    // Save to file
    const buffer = canvas.toBuffer('image/png');
    const filename = `icon${size}.png`;
    fs.writeFileSync(filename, buffer);
    console.log(`Created ${filename}`);
  }

  // Generate all sizes
  [16, 48, 128].forEach(createIcon);
  console.log('\nIcons created successfully!');

} catch (error) {
  console.error('Canvas module not installed.');
  console.error('Install with: npm install canvas');
  console.error('\nAlternatively, use the Python script or create icons manually.');
  console.error('See icons/README.md for details.');
  process.exit(1);
}
