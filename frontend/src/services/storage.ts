import { STORAGE_KEYS } from '../utils/constants';

/**
 * LocalStorage utilities
 */
class StorageService {
  /**
   * Get item from localStorage
   */
  getItem<T>(key: string): T | null {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : null;
    } catch (error) {
      console.error(`Error getting item from localStorage: ${key}`, error);
      return null;
    }
  }

  /**
   * Set item in localStorage
   */
  setItem<T>(key: string, value: T): void {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error(`Error setting item in localStorage: ${key}`, error);
    }
  }

  /**
   * Remove item from localStorage
   */
  removeItem(key: string): void {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error(`Error removing item from localStorage: ${key}`, error);
    }
  }

  /**
   * Clear all items from localStorage
   */
  clear(): void {
    try {
      localStorage.clear();
    } catch (error) {
      console.error('Error clearing localStorage', error);
    }
  }

  // Auth-specific methods
  getAuthToken(): string | null {
    return this.getItem<string>(STORAGE_KEYS.AUTH_TOKEN);
  }

  setAuthToken(token: string): void {
    this.setItem(STORAGE_KEYS.AUTH_TOKEN, token);
  }

  removeAuthToken(): void {
    this.removeItem(STORAGE_KEYS.AUTH_TOKEN);
  }

  getUserData<T>(): T | null {
    return this.getItem<T>(STORAGE_KEYS.USER_DATA);
  }

  setUserData<T>(user: T): void {
    this.setItem(STORAGE_KEYS.USER_DATA, user);
  }

  removeUserData(): void {
    this.removeItem(STORAGE_KEYS.USER_DATA);
  }

  // Dark mode
  getDarkMode(): boolean {
    const darkMode = this.getItem<boolean>(STORAGE_KEYS.DARK_MODE);
    return darkMode ?? false;
  }

  setDarkMode(enabled: boolean): void {
    this.setItem(STORAGE_KEYS.DARK_MODE, enabled);
  }
}

export const storageService = new StorageService();
