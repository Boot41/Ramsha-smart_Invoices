import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '../types/auth';
import { authApi } from '../api/auth';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

interface AuthActions {
  login: (credentials: { email: string; password: string }) => Promise<void>;
  register: (userData: { username: string; email: string; password: string }) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
  updateUser: (userData: Partial<User>) => Promise<void>;
}

type AuthStore = AuthState & AuthActions;

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      login: async (credentials) => {
        set({ isLoading: true, error: null });
        try {
          await authApi.login(credentials);
          const currentUser = authApi.getCurrentUser();
          
          set({
            user: currentUser,
            isAuthenticated: true,
            isLoading: false,
            error: null
          });
        } catch (error: any) {
          set({
            error: error.message || 'Login failed',
            isLoading: false,
            isAuthenticated: false,
            user: null
          });
          throw error;
        }
      },

      register: async (userData) => {
        set({ isLoading: true, error: null });
        try {
          await authApi.register(userData);
          set({ isLoading: false, error: null });
        } catch (error: any) {
          set({
            error: error.message || 'Registration failed',
            isLoading: false
          });
          throw error;
        }
      },

      logout: async () => {
        set({ isLoading: true });
        try {
          await authApi.logout();
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null
          });
        } catch (error: any) {
          // Even if logout fails on server, clear local state
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null
          });
        }
      },

      checkAuth: async () => {
        set({ isLoading: true });
        try {
          if (authApi.isAuthenticated()) {
            const currentUser = authApi.getCurrentUser();
            if (currentUser) {
              // Optionally fetch fresh user data from server
              try {
                const userInfo = await authApi.getCurrentUserInfo();
                set({
                  user: userInfo.user,
                  isAuthenticated: userInfo.authenticated,
                  isLoading: false,
                  error: null
                });
              } catch {
                // If server call fails, use token data
                set({
                  user: currentUser,
                  isAuthenticated: true,
                  isLoading: false,
                  error: null
                });
              }
            } else {
              set({
                user: null,
                isAuthenticated: false,
                isLoading: false,
                error: null
              });
            }
          } else {
            set({
              user: null,
              isAuthenticated: false,
              isLoading: false,
              error: null
            });
          }
        } catch (error: any) {
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: error.message || 'Authentication check failed'
          });
        }
      },

      updateUser: async (userData) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authApi.updateProfile(userData);
          set({
            user: response.profile,
            isLoading: false,
            error: null
          });
        } catch (error: any) {
          set({
            error: error.message || 'Profile update failed',
            isLoading: false
          });
          throw error;
        }
      },

      clearError: () => set({ error: null }),
      setLoading: (loading: boolean) => set({ isLoading: loading })
    }),
    {
      name: 'auth-store',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
);