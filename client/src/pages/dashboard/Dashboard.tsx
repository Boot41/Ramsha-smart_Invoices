import React from 'react';
import { Card } from '../../components/ui';
import { Link } from 'react-router-dom';
import {
  FileText,
  Calendar,
  Bot,
  Clock,
  ArrowRight,
  CheckCircle,
  Zap,
  Shield,
  BarChart3,
  Settings,
  Users,
  Mail
} from 'lucide-react';

const Dashboard: React.FC = () => {
  const features = [
    {
      icon: FileText,
      title: 'Smart Contract Analysis',
      description: 'Upload contracts and let our AI extract key billing information automatically',
      link: '/contracts',
      color: 'blue'
    },
    {
      icon: Calendar,
      title: 'Automated Scheduling',
      description: 'Set up recurring invoices based on contract terms and billing cycles',
      link: '/invoices/scheduling',
      color: 'green'
    },
    {
      icon: Bot,
      title: 'AI-Powered Validation',
      description: 'Ensure invoice accuracy with intelligent data validation and verification',
      link: '/workflow',
      color: 'purple'
    },
    {
      icon: Mail,
      title: 'Professional Templates',
      description: 'Generate beautiful, professional invoices with customizable templates',
      link: '/invoices/templates',
      color: 'orange'
    }
  ];

  const steps = [
    {
      number: '01',
      title: 'Upload Contract',
      description: 'Upload your contract document and let our AI analyze the billing terms'
    },
    {
      number: '02',
      title: 'Configure Schedule',
      description: 'Set up automated billing schedules based on contract requirements'
    },
    {
      number: '03',
      title: 'Validate & Send',
      description: 'Review AI-generated invoices and send them automatically'
    }
  ];

  const benefits = [
    {
      icon: Clock,
      title: 'Save 90% Time',
      description: 'Automate repetitive invoicing tasks'
    },
    {
      icon: Shield,
      title: 'Reduce Errors',
      description: 'AI-powered validation ensures accuracy'
    },
    {
      icon: Zap,
      title: 'Faster Payments',
      description: 'Professional invoices get paid faster'
    },
    {
      icon: BarChart3,
      title: 'Better Insights',
      description: 'Track performance with detailed analytics'
    }
  ];

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-8 text-white">
        <div className="max-w-4xl">
          <h1 className="text-4xl font-bold mb-4">Smart Invoice Scheduler</h1>
          <p className="text-xl mb-6 text-blue-100">
            Transform your contract management with AI-powered invoice automation. 
            Upload contracts, schedule invoices, and get paid faster.
          </p>
          <div className="flex flex-wrap gap-4">
            <Link 
              to="/contracts" 
              className="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-blue-50 transition-colors inline-flex items-center"
            >
              Get Started <ArrowRight className="ml-2 w-4 h-4" />
            </Link>
            <Link 
              to="/invoices/scheduling" 
              className="border border-white/30 text-white px-6 py-3 rounded-lg font-semibold hover:bg-white/10 transition-colors"
            >
              View Demo
            </Link>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Key Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <Link key={index} to={feature.link} className="group">
              <Card className="p-6 h-full hover:shadow-lg transition-all duration-200 group-hover:scale-105">
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 ${
                  feature.color === 'blue' ? 'bg-blue-100' :
                  feature.color === 'green' ? 'bg-green-100' :
                  feature.color === 'purple' ? 'bg-purple-100' :
                  'bg-orange-100'
                }`}>
                  <feature.icon className={`w-6 h-6 ${
                    feature.color === 'blue' ? 'text-blue-600' :
                    feature.color === 'green' ? 'text-green-600' :
                    feature.color === 'purple' ? 'text-purple-600' :
                    'text-orange-600'
                  }`} />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-blue-600">
                  {feature.title}
                </h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  {feature.description}
                </p>
                <ArrowRight className="w-4 h-4 text-gray-400 mt-4 group-hover:text-blue-600 group-hover:translate-x-1 transition-all" />
              </Card>
            </Link>
          ))}
        </div>
      </div>

      {/* How It Works */}
      <div className="bg-gray-50 rounded-xl p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">How It Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map((step, index) => (
            <div key={index} className="text-center">
              <div className="w-16 h-16 bg-blue-600 text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">
                {step.number}
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">{step.title}</h3>
              <p className="text-gray-600">{step.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Benefits */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Why Choose Smart Invoice Scheduler?</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {benefits.map((benefit, index) => (
            <Card key={index} className="p-6 text-center">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <benefit.icon className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{benefit.title}</h3>
              <p className="text-gray-600 text-sm">{benefit.description}</p>
            </Card>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>
            <Settings className="w-5 h-5 text-gray-400" />
          </div>
          <div className="space-y-3">
            <Link to="/contracts" className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
              <div className="flex items-center space-x-3">
                <FileText className="w-5 h-5 text-blue-600" />
                <span className="font-medium text-gray-900">Upload New Contract</span>
              </div>
              <ArrowRight className="w-4 h-4 text-gray-400" />
            </Link>
            <Link to="/invoices/scheduling" className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
              <div className="flex items-center space-x-3">
                <Calendar className="w-5 h-5 text-green-600" />
                <span className="font-medium text-gray-900">Schedule Invoices</span>
              </div>
              <ArrowRight className="w-4 h-4 text-gray-400" />
            </Link>
            <Link to="/workflow" className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
              <div className="flex items-center space-x-3">
                <Bot className="w-5 h-5 text-purple-600" />
                <span className="font-medium text-gray-900">View Workflow</span>
              </div>
              <ArrowRight className="w-4 h-4 text-gray-400" />
            </Link>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Getting Started Tips</h3>
            <Users className="w-5 h-5 text-gray-400" />
          </div>
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
              <div>
                <p className="font-medium text-gray-900">Prepare Your Contracts</p>
                <p className="text-sm text-gray-600">Have digital copies of your contracts ready for upload</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
              <div>
                <p className="font-medium text-gray-900">Set Up Templates</p>
                <p className="text-sm text-gray-600">Customize invoice templates to match your brand</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
              <div>
                <p className="font-medium text-gray-900">Configure Notifications</p>
                <p className="text-sm text-gray-600">Set up email notifications for automated workflows</p>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;