import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';
import { useAuth } from '../../../hooks/useAuth';
import type { LoginCredentials } from '../../../types';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login, isLoading, error, clearError } = useAuth();
  const [credentials, setCredentials] = useState<LoginCredentials>({
    email: '',
    password: ''
  });

  

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    try {
      await login(credentials);
      navigate('/dashboard');
    } catch (err) {
      // Error is handled by the store
      console.error('Login failed:', err);
    }
  };

  const handleChange = (field: keyof LoginCredentials) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setCredentials(prev => ({
      ...prev,
      [field]: e.target.value
    }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-2xl mb-4">
            <span className="text-2xl font-bold text-white">SI</span>
          </div>
          <h1 className="text-3xl font-bold text-white">
            Welcome Back
          </h1>
          <p className="text-slate-400 mt-2">Sign in to continue to Smart Invoice</p>
        </div>

        <Card shadow="xl" className="backdrop-blur-sm bg-white/10 border-white/20">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold text-white">Sign In</CardTitle>
            <CardDescription className="text-slate-400">
              Enter your credentials to access your account.
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-6">
              {error && (
                <div className="p-4 bg-red-900/50 border border-red-400/50 rounded-lg">
                  <p className="text-sm text-red-300">{error}</p>
                </div>
              )}

              <Input
                label="Email Address"
                type="email"
                placeholder="john@example.com"
                value={credentials.email}
                onChange={handleChange('email')}
                required
                className="mt-4"
              />

              <Input
                label="Password"
                type="password"
                placeholder="Enter your password"
                value={credentials.password}
                onChange={handleChange('password')}
                required
                className="mt-4"
              />
              
              <div className="flex items-center justify-between text-sm">
                <label className="flex items-center space-x-2 text-slate-400">
                  <input
                    type="checkbox"
                    className="w-4 h-4 text-purple-500 border-slate-600 rounded focus:ring-purple-500 bg-slate-700"
                  />
                  <span>Remember me</span>
                </label>
                <a href="#" className="text-purple-400 hover:text-purple-300 font-medium">
                  Forgot password?
                </a>
              </div>
            </CardContent>

            <CardFooter className="flex flex-col space-y-4">
              <Button
                type="submit"
                variant="gradient"
                size="lg"
                fullWidth
                loading={isLoading}
                disabled={!credentials.email || !credentials.password}
                className="from-purple-600 to-indigo-600"
              >
                {isLoading ? 'Signing in...' : 'Sign In'}
              </Button>

              <div className="text-center">
                <span className="text-slate-400">Don't have an account? </span>
                <a href="/auth/signup" className="text-purple-400 hover:text-purple-300 font-medium">
                  Sign up
                </a>
              </div>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
};

export default Login;