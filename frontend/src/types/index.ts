// User types
export interface User {
  id: string;
  email: string;
  username: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
}

// Submission types
export type SentimentType = 'positive' | 'neutral' | 'negative';

export interface Submission {
  id: string;
  user_id: string;
  audio_url: string;
  transcription: string;
  sentiment: SentimentType;
  confidence_score: number;
  duration: number;
  created_at: string;
  metadata?: Record<string, any>;
}

export interface CreateSubmissionRequest {
  audio_file: File;
  metadata?: Record<string, any>;
}

export interface SubmissionResponse {
  submission: Submission;
  message: string;
}

// Analytics types
export interface SentimentStats {
  positive: number;
  neutral: number;
  negative: number;
  total: number;
}

export interface TimeSeriesData {
  date: string;
  positive: number;
  neutral: number;
  negative: number;
  total: number;
}

export interface AnalyticsData {
  sentiment_stats: SentimentStats;
  total_submissions: number;
  average_confidence: number;
  total_duration: number;
  time_series: TimeSeriesData[];
}

// Recording types
export interface RecordingState {
  isRecording: boolean;
  isPaused: boolean;
  duration: number;
  audioBlob: Blob | null;
  audioUrl: string | null;
}

// API Error types
export interface ApiError {
  message: string;
  detail?: string;
  status?: number;
}

// Pagination
export interface PaginationParams {
  skip?: number;
  limit?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}
