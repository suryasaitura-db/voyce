import { apiClient } from './api';
import { storageService } from './storage';
import {
  AuthResponse,
  LoginCredentials,
  RegisterData,
  User,
} from '../types';
import { API_ENDPOINTS } from '../utils/constants';

/**
 * Authentication service
 */
class AuthService {
  /**
   * Login user
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const formData = new URLSearchParams();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);

    const response = await apiClient.post<AuthResponse>(
      API_ENDPOINTS.AUTH.LOGIN,
      formData,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    const { access_token, user } = response.data;

    // Store token and user data
    storageService.setAuthToken(access_token);
    storageService.setUserData(user);

    return response.data;
  }

  /**
   * Register new user
   */
  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>(
      API_ENDPOINTS.AUTH.REGISTER,
      data
    );

    const { access_token, user } = response.data;

    // Store token and user data
    storageService.setAuthToken(access_token);
    storageService.setUserData(user);

    return response.data;
  }

  /**
   * Logout user
   */
  logout(): void {
    storageService.removeAuthToken();
    storageService.removeUserData();
  }

  /**
   * Get current user
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>(API_ENDPOINTS.AUTH.ME);
    storageService.setUserData(response.data);
    return response.data;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!storageService.getAuthToken();
  }

  /**
   * Get stored user data
   */
  getStoredUser(): User | null {
    return storageService.getUserData<User>();
  }
}

export const authService = new AuthService();
