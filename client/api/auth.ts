
import type { User, UserCreate, LoginRequest, TokenResponse } from '../types/auth';
import { apiClient } from './base';
import { API_ENDPOINTS, TOKEN_STORAGE_KEY } from './config';
import { clearAllAuthData } from '../utils/auth';

export class AuthApi {
  static async login(credentials: LoginRequest): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>(
      API_ENDPOINTS.AUTH.LOGIN,
      credentials,
      { requiresAuth: false }
    );
    
    // Store token in localStorage
    if (response.access_token) {
      localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token);
    }
    
    return response;
  }

  static async register(userData: UserCreate): Promise<User> {
    return apiClient.post<User>(
      API_ENDPOINTS.AUTH.REGISTER,
      userData,
      { requiresAuth: false }
    );
  }

  static async logout(): Promise<void> {
    // Clear all auth-related data
    clearAllAuthData();
    
    // If you have a logout endpoint on the server, call it here
    // try {
    //   await apiClient.post('/auth/logout');
    // } catch (error) {
    //   // Ignore logout endpoint errors
    // }
  }

  static getToken(): string | null {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  }

  static isAuthenticated(): boolean {
    const token = this.getToken();
    if (!token) return false;
    
    try {
      // Basic token validation (you might want to add expiry check)
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      return payload.exp > currentTime;
    } catch {
      return false;
    }
  }

  static getCurrentUser(): any | null {
    const token = this.getToken();
    if (!token) return null;
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return {
        id: payload.sub,
        username: payload.username,
        email: payload.email,
        role: payload.role, // Add role from JWT payload
      };
    } catch {
      return null;
    }
  }
}

// Export instance methods for easier usage
export const authApi = {
  login: AuthApi.login.bind(AuthApi),
  register: AuthApi.register.bind(AuthApi),
  logout: AuthApi.logout.bind(AuthApi),
  getToken: AuthApi.getToken.bind(AuthApi),
  isAuthenticated: AuthApi.isAuthenticated.bind(AuthApi),
  getCurrentUser: AuthApi.getCurrentUser.bind(AuthApi),
};