import type { 
  User, 
  UserLoginRequest,
  UserLoginResponse,
  UserRegistrationRequest,
  UserRegistrationResponse,
  ChangePasswordRequest,
  ForgotPasswordRequest,
  ResetPasswordRequest,
  PasswordResetResponse,
  UpdateProfileRequest,
  UserProfileResponse,
  EmailVerificationRequest,
  VerificationResponse
} from '../types/auth';
import { apiClient } from './base';
import { API_ENDPOINTS, TOKEN_STORAGE_KEY } from './config';
import { clearAllAuthData } from '../utils/auth';

export class AuthApi {
  static async login(credentials: UserLoginRequest): Promise<UserLoginResponse> {
    const response = await apiClient.post<UserLoginResponse>(
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

  static async register(userData: UserRegistrationRequest): Promise<UserRegistrationResponse> {
    const response = await apiClient.post<UserRegistrationResponse>(
      API_ENDPOINTS.AUTH.REGISTER,
      userData,
      { requiresAuth: false }
    );
    
    // Store token in localStorage if returned (auto-login after registration)
    if (response.access_token) {
      localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token);
    }
    
    return response;
  }

  static async logout(): Promise<{ success: boolean; message: string }> {
    try {
      const response = await apiClient.post<{ success: boolean; message: string }>(
        API_ENDPOINTS.AUTH.LOGOUT,
        {}, // No data to send for logout
        { requiresAuth: true }
      );
      
      // Clear all auth-related data
      clearAllAuthData();
      
      return response;
    } catch (error) {
      // Even if the server call fails, clear local data
      clearAllAuthData();
      throw error;
    }
  }

  static async changePassword(data: ChangePasswordRequest): Promise<{ success: boolean; message: string }> {
    return apiClient.post<{ success: boolean; message: string }>(
      API_ENDPOINTS.AUTH.CHANGE_PASSWORD,
      data
    );
  }

  static async forgotPassword(data: ForgotPasswordRequest): Promise<PasswordResetResponse> {
    return apiClient.post<PasswordResetResponse>(
      API_ENDPOINTS.AUTH.FORGOT_PASSWORD,
      data,
      { requiresAuth: false }
    );
  }

  static async resetPassword(data: ResetPasswordRequest): Promise<{ success: boolean; message: string }> {
    return apiClient.post<{ success: boolean; message: string }>(
      API_ENDPOINTS.AUTH.RESET_PASSWORD,
      data,
      { requiresAuth: false }
    );
  }

  static async getProfile(): Promise<UserProfileResponse> {
    return apiClient.get<UserProfileResponse>(API_ENDPOINTS.AUTH.PROFILE);
  }

  static async updateProfile(data: UpdateProfileRequest): Promise<{ success: boolean; message: string; profile: User }> {
    return apiClient.put<{ success: boolean; message: string; profile: User }>(
      API_ENDPOINTS.AUTH.PROFILE,
      data
    );
  }

  static async verifyEmail(data: EmailVerificationRequest): Promise<VerificationResponse> {
    return apiClient.post<VerificationResponse>(
      API_ENDPOINTS.AUTH.VERIFY_EMAIL,
      data,
      { requiresAuth: false }
    );
  }

  static async getCurrentUserInfo(): Promise<{ user: User; authenticated: boolean; permissions: any }> {
    return apiClient.get<{ user: User; authenticated: boolean; permissions: any }>(
      API_ENDPOINTS.AUTH.ME
    );
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
  changePassword: AuthApi.changePassword.bind(AuthApi),
  forgotPassword: AuthApi.forgotPassword.bind(AuthApi),
  resetPassword: AuthApi.resetPassword.bind(AuthApi),
  getProfile: AuthApi.getProfile.bind(AuthApi),
  updateProfile: AuthApi.updateProfile.bind(AuthApi),
  verifyEmail: AuthApi.verifyEmail.bind(AuthApi),
  getCurrentUserInfo: AuthApi.getCurrentUserInfo.bind(AuthApi),
  getToken: AuthApi.getToken.bind(AuthApi),
  isAuthenticated: AuthApi.isAuthenticated.bind(AuthApi),
  getCurrentUser: AuthApi.getCurrentUser.bind(AuthApi),
};