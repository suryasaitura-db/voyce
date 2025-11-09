export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const APP_NAME = import.meta.env.VITE_APP_NAME || 'Voyce';
export const MAX_RECORDING_DURATION = Number(import.meta.env.VITE_MAX_RECORDING_DURATION) || 300; // 5 minutes in seconds
export const ENABLE_DARK_MODE = import.meta.env.VITE_ENABLE_DARK_MODE === 'true';

// Local storage keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'voyce_auth_token',
  USER_DATA: 'voyce_user_data',
  DARK_MODE: 'voyce_dark_mode',
} as const;

// API endpoints
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/auth/login',
    REGISTER: '/api/auth/register',
    ME: '/api/auth/me',
  },
  SUBMISSIONS: {
    CREATE: '/api/submissions',
    LIST: '/api/submissions',
    GET: (id: string) => `/api/submissions/${id}`,
    DELETE: (id: string) => `/api/submissions/${id}`,
  },
  ANALYTICS: {
    GET: '/api/analytics',
  },
} as const;

// Recording constraints
export const AUDIO_CONSTRAINTS = {
  audio: {
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true,
  },
} as const;

// Sentiment colors
export const SENTIMENT_COLORS = {
  positive: '#10b981',
  neutral: '#6b7280',
  negative: '#ef4444',
} as const;

// Chart colors
export const CHART_COLORS = {
  positive: '#10b981',
  neutral: '#3b82f6',
  negative: '#ef4444',
} as const;

// Date formats
export const DATE_FORMATS = {
  DISPLAY: 'MMM dd, yyyy',
  DISPLAY_WITH_TIME: 'MMM dd, yyyy HH:mm',
  API: 'yyyy-MM-dd',
} as const;

// Query keys for React Query
export const QUERY_KEYS = {
  SUBMISSIONS: 'submissions',
  SUBMISSION_DETAIL: 'submission-detail',
  ANALYTICS: 'analytics',
  USER: 'user',
} as const;
