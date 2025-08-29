export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: 'admin' | 'user' | 'enterprise';
  avatar?: string;
  company?: string;
  phone?: string;
  isVerified: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface UserLoginRequest {
  email: string;
  password: string;
}

export interface UserLoginResponse {
  success: boolean;
  message: string;
  access_token: string;
  token_type: string;
  user: User;
}

export interface UserRegistrationRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  company?: string;
  phone?: string;
}

export interface UserRegistrationResponse {
  success: boolean;
  message: string;
  user_id?: string;
  email: string;
  role: string;
  verification_required?: boolean;
  verification_method?: string;
  access_token?: string;
  token_type?: string;
  expires_in?: number;
  user?: User;
  permissions?: any;
}

export interface UserCreate {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  company?: string;
  phone?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user?: User;
}

export interface SignupData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
}

export interface EnterpriseSignupData extends SignupData {
  companyName: string;
  businessType: string;
  employeeCount: string;
  industry: string;
  planType: 'basic' | 'pro' | 'enterprise';
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface PasswordResetResponse {
  success: boolean;
  message: string;
}

export interface UpdateProfileRequest {
  first_name?: string;
  last_name?: string;
  company?: string;
  phone?: string;
}

export interface UserProfileResponse {
  success: boolean;
  user: User;
}

export interface EmailVerificationRequest {
  token: string;
}

export interface VerificationResponse {
  success: boolean;
  message: string;
}