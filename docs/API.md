# API Documentation

Complete REST API reference for the Voyce Voice Feedback Platform.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Request/Response Format](#requestresponse-format)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [API Endpoints](#api-endpoints)
  - [Authentication](#authentication-endpoints)
  - [Submissions](#submissions-endpoints)
  - [Analytics](#analytics-endpoints)
  - [System](#system-endpoints)

## Overview

The Voyce API is a RESTful API that uses JSON for request and response payloads. All API endpoints require authentication unless otherwise specified.

### API Version
- **Current Version**: v1
- **Base Path**: `/api`

## Authentication

The API uses OAuth2 with JWT (JSON Web Tokens) for authentication.

### Authentication Flow

1. **Register** or **Login** to get access token
2. Include token in `Authorization` header for all subsequent requests
3. Refresh token when it expires

### Token Format

```http
Authorization: Bearer <your_jwt_token>
```

### Token Expiration
- **Access Token**: 60 minutes
- **Refresh Token**: 7 days

## Base URL

```
Development: http://localhost:8000/api
Production: https://api.voyce.ai/api
```

## Request/Response Format

### Request Headers

```http
Content-Type: application/json
Authorization: Bearer <token>
Accept: application/json
```

### Response Format

**Success Response:**
```json
{
  "data": { ... },
  "message": "Success message",
  "status": "success"
}
```

**Error Response:**
```json
{
  "detail": "Error message",
  "status": "error",
  "code": "ERROR_CODE"
}
```

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request succeeded |
| 201 | Created - Resource created successfully |
| 204 | No Content - Request succeeded, no content to return |
| 400 | Bad Request - Invalid request format |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |
| 503 | Service Unavailable - Service temporarily unavailable |

### Error Response Examples

**Validation Error (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Authentication Error (401):**
```json
{
  "detail": "Invalid authentication credentials",
  "code": "INVALID_TOKEN"
}
```

## Rate Limiting

- **Authenticated Users**: 1000 requests/hour
- **Unauthenticated**: 100 requests/hour
- **File Upload**: 50 requests/hour

Rate limit headers:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640000000
```

## API Endpoints

---

## Authentication Endpoints

### Register User

Create a new user account.

**Endpoint:** `POST /api/auth/register`

**Authentication:** Not required

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePassword123!",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "is_active": true,
  "is_verified": false,
  "created_at": "2025-01-08T10:00:00Z"
}
```

---

### Login

Authenticate and receive access token.

**Endpoint:** `POST /api/auth/login`

**Authentication:** Not required

**Request Body:**
```json
{
  "username": "johndoe",
  "password": "SecurePassword123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

### Refresh Token

Get a new access token using refresh token.

**Endpoint:** `POST /api/auth/refresh`

**Authentication:** Not required

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

### Get Current User

Retrieve authenticated user information.

**Endpoint:** `GET /api/auth/me`

**Authentication:** Required

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "avatar_url": "https://...",
  "is_active": true,
  "is_verified": true,
  "role": "user",
  "created_at": "2025-01-08T10:00:00Z"
}
```

---

### Logout

Invalidate current session.

**Endpoint:** `POST /api/auth/logout`

**Authentication:** Required

**Response (204):**
No content

---

## Submissions Endpoints

### Upload Voice Submission

Upload a voice recording for processing.

**Endpoint:** `POST /api/submissions/upload`

**Authentication:** Required

**Content-Type:** `multipart/form-data`

**Request Body:**
```
file: <audio_file> (required)
title: "Product feedback" (optional)
description: "Feedback about the checkout process" (optional)
category: "feature_request" (optional)
tags: ["checkout", "ux"] (optional, JSON array)
source: "web" (optional)
source_url: "https://example.com/checkout" (optional)
```

**Supported Audio Formats:**
- WAV, MP3, M4A, OGG, FLAC
- Max size: 50MB
- Max duration: 10 minutes

**Response (201):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "file_name": "recording_2025-01-08.wav",
  "file_size": 1048576,
  "file_format": "wav",
  "duration": 45.5,
  "status": "pending",
  "created_at": "2025-01-08T10:30:00Z",
  "upload_url": "https://storage.../upload/..."
}
```

---

### List Submissions

Retrieve user's voice submissions with pagination.

**Endpoint:** `GET /api/submissions`

**Authentication:** Required

**Query Parameters:**
- `page` (integer, default: 1): Page number
- `limit` (integer, default: 20, max: 100): Items per page
- `status` (string, optional): Filter by status (pending, processing, completed, failed)
- `category` (string, optional): Filter by category
- `from_date` (ISO date, optional): Filter submissions from date
- `to_date` (ISO date, optional): Filter submissions to date
- `sort` (string, default: "created_at"): Sort field
- `order` (string, default: "desc"): Sort order (asc, desc)

**Example Request:**
```http
GET /api/submissions?page=1&limit=10&status=completed&sort=created_at&order=desc
```

**Response (200):**
```json
{
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "file_name": "recording.wav",
      "title": "Product feedback",
      "category": "feature_request",
      "status": "completed",
      "duration": 45.5,
      "created_at": "2025-01-08T10:30:00Z",
      "is_transcribed": true,
      "is_analyzed": true
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 10,
  "pages": 15
}
```

---

### Get Submission Details

Retrieve detailed information about a specific submission.

**Endpoint:** `GET /api/submissions/{submission_id}`

**Authentication:** Required

**Response (200):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "recording.wav",
  "file_size": 1048576,
  "file_format": "wav",
  "duration": 45.5,
  "sample_rate": 44100,
  "channels": 1,
  "title": "Product feedback",
  "description": "Feedback about checkout",
  "category": "feature_request",
  "tags": ["checkout", "ux"],
  "source": "web",
  "source_url": "https://example.com/checkout",
  "status": "completed",
  "is_transcribed": true,
  "is_analyzed": true,
  "created_at": "2025-01-08T10:30:00Z",
  "processed_at": "2025-01-08T10:32:00Z",
  "transcription": {
    "text": "I really like the new checkout process...",
    "language": "en",
    "confidence": 0.95,
    "word_count": 45
  },
  "analysis": {
    "sentiment": "positive",
    "sentiment_score": 0.85,
    "intent": "feedback",
    "summary": "User appreciates the new checkout...",
    "key_points": ["Likes new design", "Suggests improvement"],
    "is_actionable": true
  }
}
```

---

### Get Transcription

Retrieve full transcription for a submission.

**Endpoint:** `GET /api/submissions/{submission_id}/transcription`

**Authentication:** Required

**Response (200):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "submission_id": "660e8400-e29b-41d4-a716-446655440000",
  "text": "I really like the new checkout process. It's much faster and easier to use. However, I think the payment options could be more visible.",
  "language": "en",
  "confidence": 0.95,
  "word_count": 28,
  "speaking_rate": 120.5,
  "words": [
    {
      "word": "I",
      "start": 0.0,
      "end": 0.1,
      "confidence": 0.99
    },
    {
      "word": "really",
      "start": 0.1,
      "end": 0.4,
      "confidence": 0.98
    }
  ],
  "segments": [
    {
      "text": "I really like the new checkout process.",
      "start": 0.0,
      "end": 3.5,
      "confidence": 0.96
    }
  ],
  "model": "whisper-large-v3",
  "processing_time": 2.3,
  "created_at": "2025-01-08T10:31:00Z"
}
```

---

### Get Analysis

Retrieve AI analysis for a submission.

**Endpoint:** `GET /api/submissions/{submission_id}/analysis`

**Authentication:** Required

**Response (200):**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "submission_id": "660e8400-e29b-41d4-a716-446655440000",
  "sentiment": "positive",
  "sentiment_score": 0.85,
  "sentiment_confidence": 0.92,
  "sentiment_breakdown": {
    "positive": 0.85,
    "negative": 0.05,
    "neutral": 0.10
  },
  "emotions": {
    "joy": 0.70,
    "satisfaction": 0.60,
    "interest": 0.40
  },
  "dominant_emotion": "joy",
  "intent": "feedback",
  "intent_confidence": 0.88,
  "sub_intents": ["suggestion", "appreciation"],
  "summary": "User expresses satisfaction with the new checkout process but suggests making payment options more prominent.",
  "key_points": [
    "Appreciates faster checkout",
    "Finds it easier to use",
    "Suggests improving payment visibility"
  ],
  "action_items": [
    "Consider making payment options more visible"
  ],
  "topics": {
    "checkout_process": 0.95,
    "payment_options": 0.75,
    "user_experience": 0.80
  },
  "entities": {
    "features": ["checkout", "payment options"],
    "sentiments": ["faster", "easier"]
  },
  "clarity_score": 0.90,
  "urgency_score": 0.30,
  "importance_score": 0.75,
  "is_actionable": true,
  "requires_follow_up": false,
  "is_complaint": false,
  "is_positive_feedback": true,
  "model": "gpt-4",
  "processing_time": 1.5,
  "created_at": "2025-01-08T10:32:00Z"
}
```

---

### Update Submission

Update submission metadata.

**Endpoint:** `PATCH /api/submissions/{submission_id}`

**Authentication:** Required

**Request Body:**
```json
{
  "title": "Updated title",
  "description": "Updated description",
  "category": "bug_report",
  "tags": ["bug", "urgent"],
  "is_public": false
}
```

**Response (200):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "title": "Updated title",
  "description": "Updated description",
  "category": "bug_report",
  "tags": ["bug", "urgent"],
  "is_public": false,
  "updated_at": "2025-01-08T11:00:00Z"
}
```

---

### Delete Submission

Delete a voice submission and all associated data.

**Endpoint:** `DELETE /api/submissions/{submission_id}`

**Authentication:** Required

**Response (204):**
No content

---

## Analytics Endpoints

### Dashboard Overview

Get summary statistics for the dashboard.

**Endpoint:** `GET /api/analytics/dashboard`

**Authentication:** Required

**Query Parameters:**
- `from_date` (ISO date, optional): Start date for metrics
- `to_date` (ISO date, optional): End date for metrics

**Response (200):**
```json
{
  "total_submissions": 1250,
  "completed_submissions": 1180,
  "pending_submissions": 45,
  "failed_submissions": 25,
  "total_duration_minutes": 15420.5,
  "avg_processing_time_seconds": 3.2,
  "sentiment_distribution": {
    "positive": 65,
    "neutral": 25,
    "negative": 10
  },
  "intent_distribution": {
    "feedback": 45,
    "suggestion": 30,
    "complaint": 15,
    "question": 10
  },
  "submissions_by_day": [
    {
      "date": "2025-01-01",
      "count": 42
    },
    {
      "date": "2025-01-02",
      "count": 38
    }
  ],
  "top_categories": [
    {
      "category": "feature_request",
      "count": 320
    },
    {
      "category": "bug_report",
      "count": 180
    }
  ]
}
```

---

### Sentiment Trends

Get sentiment analysis trends over time.

**Endpoint:** `GET /api/analytics/sentiment-trends`

**Authentication:** Required

**Query Parameters:**
- `from_date` (ISO date, required): Start date
- `to_date` (ISO date, required): End date
- `interval` (string, default: "day"): Aggregation interval (hour, day, week, month)

**Response (200):**
```json
{
  "trends": [
    {
      "date": "2025-01-01",
      "positive": 28,
      "neutral": 10,
      "negative": 4,
      "avg_score": 0.72
    },
    {
      "date": "2025-01-02",
      "positive": 25,
      "neutral": 8,
      "negative": 5,
      "avg_score": 0.68
    }
  ],
  "overall": {
    "avg_sentiment_score": 0.70,
    "total_analyzed": 850,
    "positive_percentage": 65.5,
    "neutral_percentage": 23.2,
    "negative_percentage": 11.3
  }
}
```

---

### Top Keywords

Get most frequently mentioned keywords.

**Endpoint:** `GET /api/analytics/keywords`

**Authentication:** Required

**Query Parameters:**
- `limit` (integer, default: 20): Number of keywords to return
- `from_date` (ISO date, optional): Start date
- `to_date` (ISO date, optional): End date
- `sentiment` (string, optional): Filter by sentiment (positive, negative, neutral)

**Response (200):**
```json
{
  "keywords": [
    {
      "keyword": "checkout",
      "count": 156,
      "sentiment_avg": 0.75,
      "trending": true
    },
    {
      "keyword": "payment",
      "count": 134,
      "sentiment_avg": 0.45,
      "trending": false
    },
    {
      "keyword": "shipping",
      "count": 98,
      "sentiment_avg": -0.20,
      "trending": true
    }
  ]
}
```

---

### Export Analytics

Export analytics data in various formats.

**Endpoint:** `GET /api/analytics/export`

**Authentication:** Required

**Query Parameters:**
- `format` (string, required): Export format (csv, json, xlsx)
- `from_date` (ISO date, required): Start date
- `to_date` (ISO date, required): End date
- `include` (array, optional): Data to include (submissions, transcriptions, analyses)

**Response (200):**
Returns file download with appropriate content-type.

---

## System Endpoints

### Health Check

Check API health status.

**Endpoint:** `GET /health`

**Authentication:** Not required

**Response (200):**
```json
{
  "status": "healthy",
  "environment": "production",
  "database": "postgresql",
  "version": "1.0.0",
  "timestamp": "2025-01-08T10:00:00Z"
}
```

---

### Metrics

Prometheus metrics endpoint.

**Endpoint:** `GET /metrics`

**Authentication:** Not required

**Response (200):**
Returns Prometheus-formatted metrics.

---

### API Documentation

Interactive API documentation (development only).

**Endpoint:** `GET /api/docs`

**Authentication:** Not required

Opens Swagger UI for API exploration.

---

## Webhooks

Configure webhooks to receive real-time notifications.

### Webhook Events

- `submission.created` - New submission uploaded
- `submission.completed` - Processing completed
- `submission.failed` - Processing failed
- `transcription.completed` - Transcription finished
- `analysis.completed` - Analysis finished

### Webhook Payload Example

```json
{
  "event": "submission.completed",
  "timestamp": "2025-01-08T10:32:00Z",
  "data": {
    "submission_id": "660e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "user_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

## SDKs and Client Libraries

### Python SDK

```python
from voyce import VoyceClient

client = VoyceClient(api_key="your_api_key")

# Upload audio
submission = client.submissions.upload("recording.wav")

# Get analysis
analysis = client.submissions.get_analysis(submission.id)
```

### JavaScript SDK

```javascript
import { VoyceClient } from '@voyce/sdk';

const client = new VoyceClient({ apiKey: 'your_api_key' });

// Upload audio
const submission = await client.submissions.upload(audioFile);

// Get analysis
const analysis = await client.submissions.getAnalysis(submission.id);
```

## Best Practices

1. **Always validate input** before sending to API
2. **Handle rate limits** gracefully with exponential backoff
3. **Cache responses** when appropriate
4. **Use webhooks** for real-time updates instead of polling
5. **Implement proper error handling** for all API calls
6. **Keep tokens secure** and never commit them to version control
7. **Use pagination** for list endpoints
8. **Monitor API usage** to stay within rate limits
