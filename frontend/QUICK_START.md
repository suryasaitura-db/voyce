# Quick Start Guide

## Installation

```bash
# Navigate to the frontend directory
cd /Users/suryasai.turaga/voyce/frontend

# Install dependencies
npm install
```

## Development

```bash
# Start the development server
npm run dev
```

The application will be available at: **http://localhost:3000**

## Build for Production

```bash
# Create production build
npm run build

# Preview production build
npm run preview
```

## Environment Variables

The application uses the following environment variables (already configured in `.env`):

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Voyce
VITE_MAX_RECORDING_DURATION=300
VITE_ENABLE_DARK_MODE=true
```

## Prerequisites

Before starting the frontend, ensure:
1. Backend API is running on `http://localhost:8000`
2. Node.js 18+ is installed
3. npm is installed

## Available Routes

- `/` - Home page
- `/login` - User login
- `/register` - User registration
- `/record` - Voice recording (protected)
- `/submissions` - View submissions (protected)
- `/dashboard` - Analytics dashboard (protected)

## Features

### Voice Recording
- Click the microphone button on the Record page
- Real-time waveform visualization
- Pause/resume functionality
- Auto-submit after recording

### Analytics
- Sentiment distribution charts
- Trends over time
- Key metrics overview
- Interactive visualizations

### Authentication
- JWT-based authentication
- Protected routes
- Persistent sessions

## Troubleshooting

### Cannot connect to API
- Ensure backend is running on port 8000
- Check VITE_API_BASE_URL in .env

### Microphone access denied
- Allow microphone permissions in browser
- Check browser settings

### Build errors
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Tech Stack

- React 18
- TypeScript
- Vite
- Tailwind CSS
- React Router
- TanStack Query
- Recharts
- Axios
- Web Audio API
