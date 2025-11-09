# Voyce Frontend

A modern React web application for the Voyce voice feedback platform with AI-powered sentiment analysis.

## Features

- Voice recording with real-time waveform visualization
- Audio playback controls
- AI-powered transcription and sentiment analysis
- Analytics dashboard with interactive charts
- User authentication (login/register)
- Responsive design with Tailwind CSS
- Dark mode support
- TypeScript for type safety

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **TanStack Query** - Data fetching and caching
- **Tailwind CSS** - Utility-first CSS framework
- **Recharts** - Analytics charts
- **Axios** - HTTP client
- **Web Audio API** - Voice recording

## Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

## Installation

1. Install dependencies:
```bash
npm install
```

2. Copy environment variables:
```bash
cp .env.example .env
```

3. Update `.env` if needed:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Voyce
VITE_MAX_RECORDING_DURATION=300
VITE_ENABLE_DARK_MODE=true
```

## Development

Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## Build

Build for production:
```bash
npm run build
```

Preview production build:
```bash
npm run preview
```

## Project Structure

```
frontend/
├── public/              # Static files
├── src/
│   ├── components/     # Reusable UI components
│   │   ├── Navbar.tsx
│   │   ├── VoiceRecorder.tsx
│   │   ├── AudioPlayer.tsx
│   │   ├── SubmissionCard.tsx
│   │   ├── SentimentBadge.tsx
│   │   ├── AnalyticsChart.tsx
│   │   └── ProtectedRoute.tsx
│   ├── pages/          # Page components
│   │   ├── HomePage.tsx
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   ├── RecordPage.tsx
│   │   ├── SubmissionsPage.tsx
│   │   └── DashboardPage.tsx
│   ├── hooks/          # Custom React hooks
│   │   ├── useAuth.tsx
│   │   ├── useRecorder.ts
│   │   └── useSubmissions.ts
│   ├── services/       # API and storage services
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   └── storage.ts
│   ├── types/          # TypeScript type definitions
│   │   └── index.ts
│   ├── utils/          # Utility functions
│   │   ├── constants.ts
│   │   └── helpers.ts
│   ├── App.tsx         # Main app component
│   ├── main.tsx        # App entry point
│   └── index.css       # Global styles
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── vite.config.ts
└── README.md
```

## Key Features

### Voice Recording
- Real-time waveform visualization during recording
- Pause/resume functionality
- Maximum recording duration limit
- Audio preview before submission

### Authentication
- JWT-based authentication
- Protected routes
- Persistent login with localStorage

### Analytics
- Sentiment distribution pie chart
- Sentiment trends over time
- Interactive bar charts
- Key metrics overview

### Data Management
- TanStack Query for efficient data fetching
- Automatic cache invalidation
- Optimistic UI updates

## API Integration

The frontend connects to the backend API at `http://localhost:8000` with the following endpoints:

- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/auth/me` - Get current user
- `POST /api/submissions` - Create submission
- `GET /api/submissions` - List submissions
- `DELETE /api/submissions/:id` - Delete submission
- `GET /api/analytics` - Get analytics data

## License

MIT
