import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { useAuth } from '../../../hooks/useAuth';
import type { SignupData } from '../../../types';

const Signup: React.FC = () => {
  const navigate = useNavigate();
  const { register, isLoading, error, clearError, isAuthenticated } = useAuth();
  const [formData, setFormData] = useState<SignupData>({
    email: '',
    password: '',
    firstName: '',
    lastName: ''
  });
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<Partial<SignupData & { confirmPassword: string }>>({});

  const validateForm = (): boolean => {
    const newErrors: Partial<SignupData & { confirmPassword: string }> = {};

    if (!formData.firstName) newErrors.firstName = 'First name is required';
    if (!formData.lastName) newErrors.lastName = 'Last name is required';
    if (!formData.email) newErrors.email = 'Email is required';
    else if (!/\S+@\S+\.\S+/.test(formData.email)) newErrors.email = 'Email is invalid';
    
    if (!formData.password) newErrors.password = 'Password is required';
    else if (formData.password.length < 8) newErrors.password = 'Password must be at least 8 characters';
    
    if (!confirmPassword) newErrors.confirmPassword = 'Please confirm your password';
    else if (formData.password !== confirmPassword) newErrors.confirmPassword = 'Passwords do not match';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    clearError();

    try {
      await register({
        email: formData.email,
        password: formData.password,
        first_name: formData.firstName,
        last_name: formData.lastName
      });
      
      // Check if user is now authenticated (auto-login after registration)
      // If authenticated, go to dashboard; otherwise go to login
      if (isAuthenticated) {
        navigate('/dashboard');
      } else {
        navigate('/auth/login', { 
          state: { message: 'Account created successfully! Please login.' }
        });
      }
    } catch (err: any) {
      setErrors({ email: err.message || 'Registration failed' });
    }
  };

  const handleChange = (field: keyof SignupData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData(prev => ({
      ...prev,
      [field]: e.target.value
    }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: undefined
      }));
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-green-500 to-blue-600 rounded-2xl mb-4">
            <span className="text-2xl font-bold text-white">SI</span>
          </div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
            Join Smart Invoice
          </h1>
          <p className="text-slate-600 mt-2">Create your account and start managing invoices</p>
        </div>

        <Card shadow="xl" className="backdrop-blur-sm bg-white/80 border-white/20">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold text-slate-800">Create Account</CardTitle>
            <CardDescription className="text-slate-600">
              Fill in your details to get started
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-6">
              {/* Global error message */}
              {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              )}
              {/* Personal Information */}
              <div>
                <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center">
                  <span className="bg-gradient-to-r from-green-500 to-blue-500 bg-clip-text text-transparent mr-2">
                    👤
                  </span>
                  Personal Information
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="First Name"
                    placeholder="John"
                    value={formData.firstName}
                    onChange={handleChange('firstName')}
                    error={errors.firstName}
                    required
                  />
                  <Input
                    label="Last Name"
                    placeholder="Doe"
                    value={formData.lastName}
                    onChange={handleChange('lastName')}
                    error={errors.lastName}
                    required
                  />
                </div>
                <Input
                  label="Email Address"
                  type="email"
                  placeholder="john@example.com"
                  value={formData.email}
                  onChange={handleChange('email')}
                  error={errors.email}
                  required
                  className="mt-4"
                />
              </div>


              {/* Security */}
              <div>
                <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center">
                  <span className="bg-gradient-to-r from-green-500 to-blue-500 bg-clip-text text-transparent mr-2">
                    🔒
                  </span>
                  Security
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Password"
                    type="password"
                    placeholder="Create a strong password"
                    value={formData.password}
                    onChange={handleChange('password')}
                    error={errors.password}
                    hint="At least 8 characters"
                    required
                  />
                  <Input
                    label="Confirm Password"
                    type="password"
                    placeholder="Confirm your password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    error={errors.confirmPassword}
                    required
                  />
                </div>
              </div>

              {/* Terms and Conditions */}
              <div className="flex items-start space-x-3 p-4 bg-slate-50 rounded-lg">
                <input
                  type="checkbox"
                  id="terms"
                  required
                  className="w-4 h-4 text-green-600 border-slate-300 rounded focus:ring-green-500 mt-0.5"
                />
                <label htmlFor="terms" className="text-sm text-slate-600">
                  I agree to the{' '}
                  <a href="#" className="text-green-600 hover:text-green-700 font-medium">
                    Terms of Service
                  </a>{' '}
                  and{' '}
                  <a href="#" className="text-green-600 hover:text-green-700 font-medium">
                    Privacy Policy
                  </a>
                </label>
              </div>
            </CardContent>

            <CardFooter className="flex flex-col space-y-4">
              <Button
                type="submit"
                variant="gradient"
                size="lg"
                fullWidth
                loading={isLoading}
              >
                {isLoading ? 'Creating Account...' : 'Create Account'}
              </Button>

              <div className="text-center">
                <span className="text-slate-600">Already have an account? </span>
                <a href="/auth/login" className="text-green-600 hover:text-green-700 font-medium">
                  Sign in
                </a>
              </div>
            </CardFooter>
          </form>
        </Card>

        {/* Features */}
        <div className="mt-8 text-center">
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="flex flex-col items-center">
              <Badge variant="success" size="md" className="mb-2">✨ Free Start</Badge>
              <p className="text-sm text-slate-600">No credit card required</p>
            </div>
            <div className="flex flex-col items-center">
              <Badge variant="info" size="md" className="mb-2">🚀 Quick Setup</Badge>
              <p className="text-sm text-slate-600">Ready in 2 minutes</p>
            </div>
            <div className="flex flex-col items-center">
              <Badge variant="purple" size="md" className="mb-2">🔒 Secure</Badge>
              <p className="text-sm text-slate-600">Bank-level security</p>
            </div>
          </div>
        </div>

        {/* Enterprise Link */}
        <div className="mt-6 text-center p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg">
          <p className="text-slate-700 font-medium mb-2">Need an enterprise solution?</p>
          <a href="/auth/enterprise-signup" className="text-indigo-600 hover:text-indigo-700 font-semibold">
            Explore Enterprise Plans →
          </a>
        </div>
      </div>
    </div>
  );
};

export default Signup;