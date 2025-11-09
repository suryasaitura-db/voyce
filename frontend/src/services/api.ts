import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { API_BASE_URL } from '../utils/constants';
import { storageService } from './storage';
import { ApiError } from '../types';

/**
 * Create axios instance with base configuration
 */
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
    timeout: 30000,
  });

  // Request interceptor to add auth token
  client.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const token = storageService.getAuthToken();
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error: AxiosError) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor to handle errors
  client.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
      const apiError: ApiError = {
        message: 'An error occurred',
        status: error.response?.status,
      };

      if (error.response) {
        // Server responded with error status
        const data = error.response.data as any;
        apiError.message = data?.message || data?.detail || error.message;
        apiError.detail = data?.detail;

        // Handle 401 Unauthorized
        if (error.response.status === 401) {
          storageService.removeAuthToken();
          storageService.removeUserData();
          window.location.href = '/login';
        }
      } else if (error.request) {
        // Request was made but no response
        apiError.message = 'No response from server';
      } else {
        // Error setting up request
        apiError.message = error.message;
      }

      return Promise.reject(apiError);
    }
  );

  return client;
};

export const apiClient = createApiClient();

/**
 * Create FormData API client for file uploads
 */
export const createFormDataClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 60000, // Longer timeout for file uploads
  });

  // Add auth token
  client.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const token = storageService.getAuthToken();
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error: AxiosError) => {
      return Promise.reject(error);
    }
  );

  return client;
};

export const formDataClient = createFormDataClient();
