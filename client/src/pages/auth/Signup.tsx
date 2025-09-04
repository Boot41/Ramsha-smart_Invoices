import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useAuth } from '../../../hooks/useAuth';
import type { SignupData } from '../../../types';
import { Sun, Moon } from 'lucide-react';

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
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

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
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: undefined
      }));
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center transition-colors duration-300">
      <div className="container mx-auto p-4">
        <div className="flex flex-col lg:flex-row w-full lg:w-10/12 xl:w-10/12 bg-white dark:bg-gray-800 rounded-xl mx-auto shadow-lg overflow-hidden">
          {/* Left Side - Illustration */}
          <div className="w-full lg:w-1/2 flex-col items-center justify-center p-12 bg-gradient-to-br from-purple-600 to-indigo-600 text-white hidden lg:flex">
            <div className="text-center">
              <h1 className="text-4xl font-bold mb-4">Join Smart Invoice</h1>
              <p className="text-lg mb-8">Create your account to start automating your invoicing process.</p>
              <div className="w-48 h-48 bg-white/20 rounded-full mx-auto flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-24 h-24 text-white/50" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="17" y1="11" x2="23" y2="11"></line></svg>
              </div>
            </div>
          </div>

          {/* Right Side - Form */}
          <div className="w-full lg:w-1/2 py-12 px-12 relative">
            <button onClick={toggleTheme} className="absolute top-4 right-4 p-2 rounded-full text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700">
              {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
            </button>

            <h2 className="text-3xl mb-4 font-bold text-gray-800 dark:text-white">Create Account</h2>
            <p className="mb-4 text-gray-600 dark:text-gray-400">
              Fill in your details to get started.
            </p>

            <form onSubmit={handleSubmit}>
              <div className="space-y-4">
                {error && (
                  <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-500/30 rounded-lg">
                    <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                  </div>
                )}
                
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
                />
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

                <div className="flex items-start space-x-3">
                  <input
                    type="checkbox"
                    id="terms"
                    required
                    className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 mt-1 dark:bg-gray-700 dark:border-gray-600"
                  />
                  <label htmlFor="terms" className="text-sm text-gray-600 dark:text-gray-400">
                    I agree to the{' '}
                    <a href="#" className="text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 font-medium">
                      Terms of Service
                    </a>{' '}
                    and{' '}
                    <a href="#" className="text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 font-medium">
                      Privacy Policy
                    </a>
                  </label>
                </div>

                <Button
                  type="submit"
                  variant="gradient"
                  size="lg"
                  fullWidth
                  loading={isLoading}
                  className="from-purple-600 to-indigo-600"
                >
                  {isLoading ? 'Creating Account...' : 'Create Account'}
                </Button>

                <div className="text-center text-sm text-gray-600 dark:text-gray-400">
                  Already have an account?{' '}
                  <a href="/auth/login" className="text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 font-medium">
                    Sign in
                  </a>
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Signup;