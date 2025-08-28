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

export interface SignupData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  company?: string;
  phone?: string;
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