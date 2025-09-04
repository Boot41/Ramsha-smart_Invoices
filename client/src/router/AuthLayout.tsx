import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { authApi } from '../api/auth';
import { Layout } from '../components/shared';

export const AuthLayout: React.FC = () => {
  const { isAuthenticated: isAuthenticatedFromStore, logout } = useAuthStore();
  const isAuthenticatedFromApi = authApi.isAuthenticated();

  React.useEffect(() => {
    // If the store thinks we are authenticated but the token is invalid, log out.
    if (isAuthenticatedFromStore && !isAuthenticatedFromApi) {
      logout();
    }
  }, [isAuthenticatedFromStore, isAuthenticatedFromApi, logout]);

  if (!isAuthenticatedFromStore || !isAuthenticatedFromApi) {
    return <Navigate to="/auth/login" replace />;
  }

  return <Layout />;
};
