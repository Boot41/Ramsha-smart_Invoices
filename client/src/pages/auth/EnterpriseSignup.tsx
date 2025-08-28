import React, { useState } from 'react';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Textarea } from '../../components/ui/Textarea';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import type { EnterpriseSignupData, SelectOption } from '../../../types';

const EnterpriseSignup: React.FC = () => {
  const [formData, setFormData] = useState<EnterpriseSignupData>({
    email: '',
    password: '',
    firstName: '',
    lastName: '',
    company: '',
    phone: '',
    companyName: '',
    businessType: '',
    employeeCount: '',
    industry: '',
    planType: 'enterprise'
  });
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [errors, setErrors] = useState<Partial<EnterpriseSignupData>>({});
  console.log('Errors state:', errors); // For development

  const businessTypes: SelectOption[] = [
    { value: 'corporation', label: 'Corporation' },
    { value: 'llc', label: 'Limited Liability Company (LLC)' },
    { value: 'partnership', label: 'Partnership' },
    { value: 'sole_proprietorship', label: 'Sole Proprietorship' },
    { value: 'nonprofit', label: 'Non-profit Organization' },
    { value: 'other', label: 'Other' }
  ];

  const employeeCountOptions: SelectOption[] = [
    { value: '1-10', label: '1-10 employees' },
    { value: '11-50', label: '11-50 employees' },
    { value: '51-100', label: '51-100 employees' },
    { value: '101-500', label: '101-500 employees' },
    { value: '501-1000', label: '501-1000 employees' },
    { value: '1000+', label: '1000+ employees' }
  ];

  const industryOptions: SelectOption[] = [
    { value: 'technology', label: 'Technology' },
    { value: 'healthcare', label: 'Healthcare' },
    { value: 'finance', label: 'Financial Services' },
    { value: 'retail', label: 'Retail & E-commerce' },
    { value: 'manufacturing', label: 'Manufacturing' },
    { value: 'education', label: 'Education' },
    { value: 'consulting', label: 'Consulting' },
    { value: 'real_estate', label: 'Real Estate' },
    { value: 'other', label: 'Other' }
  ];

  const planOptions: SelectOption[] = [
    { value: 'pro', label: 'Professional Plan' },
    { value: 'enterprise', label: 'Enterprise Plan' }
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Mock enterprise signup logic
      console.log('Enterprise signup attempt:', formData);
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Simulate success
      alert('Enterprise account request submitted! Our team will contact you within 24 hours.');
    } catch (err) {
      setErrors({ email: 'Error submitting request. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: keyof EnterpriseSignupData) => (
    value: string | React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const newValue = typeof value === 'string' ? value : value.target.value;
    setFormData(prev => ({
      ...prev,
      [field]: newValue
    }));
  };

  const nextStep = () => {
    setCurrentStep(prev => Math.min(prev + 1, 3));
  };

  const prevStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center">
                <span className="bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent mr-2">
                  👤
                </span>
                Contact Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="First Name"
                  placeholder="John"
                  value={formData.firstName}
                  onChange={handleChange('firstName')}
                  required
                />
                <Input
                  label="Last Name"
                  placeholder="Doe"
                  value={formData.lastName}
                  onChange={handleChange('lastName')}
                  required
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <Input
                  label="Business Email"
                  type="email"
                  placeholder="john@company.com"
                  value={formData.email}
                  onChange={handleChange('email')}
                  required
                />
                <Input
                  label="Phone Number"
                  type="tel"
                  placeholder="+1 (555) 000-0000"
                  value={formData.phone}
                  onChange={handleChange('phone')}
                  required
                />
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center">
                <span className="bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent mr-2">
                  🏢
                </span>
                Company Information
              </h3>
              <div className="space-y-4">
                <Input
                  label="Company Name"
                  placeholder="Your Company Inc."
                  value={formData.companyName}
                  onChange={handleChange('companyName')}
                  required
                />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Select
                    label="Business Type"
                    options={businessTypes}
                    placeholder="Select business type"
                    value={formData.businessType}
                    onChange={handleChange('businessType')}
                    required
                  />
                  <Select
                    label="Number of Employees"
                    options={employeeCountOptions}
                    placeholder="Select company size"
                    value={formData.employeeCount}
                    onChange={handleChange('employeeCount')}
                    required
                  />
                </div>
                <Select
                  label="Industry"
                  options={industryOptions}
                  placeholder="Select your industry"
                  value={formData.industry}
                  onChange={handleChange('industry')}
                  required
                />
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center">
                <span className="bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent mr-2">
                  🎯
                </span>
                Plan Selection & Security
              </h3>
              <div className="space-y-4">
                <Select
                  label="Plan Type"
                  options={planOptions}
                  placeholder="Select your plan"
                  value={formData.planType}
                  onChange={handleChange('planType')}
                  required
                />
                <Input
                  label="Password"
                  type="password"
                  placeholder="Create a secure password"
                  value={formData.password}
                  onChange={handleChange('password')}
                  hint="At least 8 characters with numbers and symbols"
                  required
                />
                <Textarea
                  label="Additional Requirements"
                  placeholder="Tell us about any specific requirements or questions you have..."
                  rows={4}
                  hint="Optional - Help us prepare for your consultation call"
                />
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 flex items-center justify-center p-4">
      <div className="w-full max-w-3xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-purple-500 to-pink-600 rounded-3xl mb-4">
            <span className="text-2xl font-bold text-white">E</span>
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
            Enterprise Solutions
          </h1>
          <p className="text-slate-600 mt-2">Scale your business with our premium features</p>
          
          {/* Features Preview */}
          <div className="flex flex-wrap justify-center gap-3 mt-6">
            <Badge variant="purple" size="md">Advanced Analytics</Badge>
            <Badge variant="info" size="md">Priority Support</Badge>
            <Badge variant="success" size="md">Custom Integrations</Badge>
            <Badge variant="orange" size="md">Dedicated Manager</Badge>
          </div>
        </div>

        <Card shadow="xl" className="backdrop-blur-sm bg-white/80 border-white/20">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-2xl font-bold text-slate-800">
                  Get Started with Enterprise
                </CardTitle>
                <CardDescription className="text-slate-600">
                  Step {currentStep} of 3 - {
                    currentStep === 1 ? 'Contact Information' :
                    currentStep === 2 ? 'Company Details' :
                    'Plan & Security'
                  }
                </CardDescription>
              </div>
              <div className="text-right">
                <div className="text-sm text-slate-500 mb-1">Progress</div>
                <div className="flex space-x-1">
                  {[1, 2, 3].map((step) => (
                    <div
                      key={step}
                      className={`w-8 h-2 rounded-full ${
                        step <= currentStep
                          ? 'bg-gradient-to-r from-purple-500 to-pink-500'
                          : 'bg-slate-200'
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent>
              {renderStep()}
            </CardContent>

            <CardFooter className="flex justify-between">
              {currentStep > 1 && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={prevStep}
                >
                  Previous
                </Button>
              )}
              
              <div className="flex-1" />
              
              {currentStep < 3 ? (
                <Button
                  type="button"
                  variant="primary"
                  onClick={nextStep}
                >
                  Next Step
                </Button>
              ) : (
                <Button
                  type="submit"
                  variant="gradient"
                  loading={loading}
                  size="lg"
                >
                  {loading ? 'Submitting Request...' : 'Submit Enterprise Request'}
                </Button>
              )}
            </CardFooter>
          </form>
        </Card>

        {/* Benefits */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="text-center p-6 bg-gradient-to-br from-purple-50 to-white border-purple-200">
            <div className="text-3xl mb-3">🚀</div>
            <h3 className="font-semibold text-slate-800 mb-2">Fast Implementation</h3>
            <p className="text-sm text-slate-600">Get up and running in days, not months</p>
          </Card>
          
          <Card className="text-center p-6 bg-gradient-to-br from-blue-50 to-white border-blue-200">
            <div className="text-3xl mb-3">📞</div>
            <h3 className="font-semibold text-slate-800 mb-2">24/7 Support</h3>
            <p className="text-sm text-slate-600">Dedicated support team at your service</p>
          </Card>
          
          <Card className="text-center p-6 bg-gradient-to-br from-green-50 to-white border-green-200">
            <div className="text-3xl mb-3">🔧</div>
            <h3 className="font-semibold text-slate-800 mb-2">Custom Solutions</h3>
            <p className="text-sm text-slate-600">Tailored to your specific business needs</p>
          </Card>
        </div>

        {/* Back to regular signup */}
        <div className="mt-6 text-center">
          <span className="text-slate-600">Need a simpler plan? </span>
          <a href="/auth/signup" className="text-purple-600 hover:text-purple-700 font-medium">
            Try our Standard Signup
          </a>
        </div>
      </div>
    </div>
  );
};

export default EnterpriseSignup;