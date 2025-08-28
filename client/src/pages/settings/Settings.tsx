import React, { useState } from 'react';
import { Card, Button, Badge } from '../../components/ui';
import { 
  Palette, 
  Mail, 
  Bell, 
  Shield, 
  User, 
  CreditCard,
  Moon,
  Sun,
  Monitor
} from 'lucide-react';

const Settings: React.FC = () => {
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('light');
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [reminderNotifications, setReminderNotifications] = useState(true);
  const [selectedEmailTemplate, setSelectedEmailTemplate] = useState('professional');

  const settingsSections = [
    {
      id: 'appearance',
      title: 'Appearance',
      description: 'Customize how the application looks',
      icon: Palette,
      settings: [
        {
          name: 'Theme',
          description: 'Choose your preferred theme',
          component: (
            <div className="flex space-x-2">
              {(['light', 'dark', 'system'] as const).map((themeOption) => (
                <Button
                  key={themeOption}
                  variant={theme === themeOption ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setTheme(themeOption)}
                  className="flex items-center space-x-1"
                >
                  {themeOption === 'light' && <Sun className="w-4 h-4" />}
                  {themeOption === 'dark' && <Moon className="w-4 h-4" />}
                  {themeOption === 'system' && <Monitor className="w-4 h-4" />}
                  <span className="capitalize">{themeOption}</span>
                </Button>
              ))}
            </div>
          )
        }
      ]
    },
    {
      id: 'email-templates',
      title: 'Email Templates',
      description: 'Configure email templates for invoices and reminders',
      icon: Mail,
      settings: [
        {
          name: 'Default Template',
          description: 'Choose the default email template style',
          component: (
            <select
              value={selectedEmailTemplate}
              onChange={(e) => setSelectedEmailTemplate(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="professional">Professional</option>
              <option value="modern">Modern</option>
              <option value="minimal">Minimal</option>
              <option value="friendly">Friendly</option>
            </select>
          )
        },
        {
          name: 'Template Preview',
          description: 'Preview and customize email templates',
          component: (
            <Button variant="outline" size="sm">
              Customize Templates
            </Button>
          )
        }
      ]
    },
    {
      id: 'notifications',
      title: 'Notifications & Reminders',
      description: 'Control when and how you receive notifications',
      icon: Bell,
      settings: [
        {
          name: 'Email Notifications',
          description: 'Receive notifications via email',
          component: (
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={emailNotifications}
                onChange={(e) => setEmailNotifications(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span>{emailNotifications ? 'Enabled' : 'Disabled'}</span>
            </label>
          )
        },
        {
          name: 'Payment Reminders',
          description: 'Automatically send payment reminders',
          component: (
            <div className="flex items-center space-x-3">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={reminderNotifications}
                  onChange={(e) => setReminderNotifications(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span>{reminderNotifications ? 'Enabled' : 'Disabled'}</span>
              </label>
              {reminderNotifications && (
                <Badge variant="secondary">3 days before due</Badge>
              )}
            </div>
          )
        },
        {
          name: 'Reminder Schedule',
          description: 'Configure when reminders are sent',
          component: (
            <Button variant="outline" size="sm" disabled={!reminderNotifications}>
              Configure Schedule
            </Button>
          )
        }
      ]
    },
    {
      id: 'account',
      title: 'Account Settings',
      description: 'Manage your account information and security',
      icon: User,
      settings: [
        {
          name: 'Profile Information',
          description: 'Update your personal information',
          component: (
            <Button variant="outline" size="sm">
              Edit Profile
            </Button>
          )
        },
        {
          name: 'Security',
          description: 'Password and two-factor authentication',
          component: (
            <div className="flex space-x-2">
              <Button variant="outline" size="sm">
                Change Password
              </Button>
              <Badge variant="success">2FA Enabled</Badge>
            </div>
          )
        }
      ]
    },
    {
      id: 'billing',
      title: 'Billing & Subscription',
      description: 'Manage your subscription and payment methods',
      icon: CreditCard,
      settings: [
        {
          name: 'Current Plan',
          description: 'Professional Plan - $29/month',
          component: (
            <div className="flex items-center space-x-2">
              <Badge variant="default">Professional</Badge>
              <Button variant="outline" size="sm">
                Upgrade
              </Button>
            </div>
          )
        },
        {
          name: 'Payment Method',
          description: 'Manage your payment methods',
          component: (
            <Button variant="outline" size="sm">
              Update Payment
            </Button>
          )
        }
      ]
    }
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-2">Manage your account and application preferences</p>
      </div>

      <div className="space-y-6">
        {settingsSections.map((section) => (
          <Card key={section.id} className="p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-blue-100 rounded-lg">
                <section.icon className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{section.title}</h3>
                <p className="text-sm text-gray-600">{section.description}</p>
              </div>
            </div>

            <div className="space-y-4">
              {section.settings.map((setting, index) => (
                <div key={index} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-b-0">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{setting.name}</h4>
                    <p className="text-sm text-gray-600">{setting.description}</p>
                  </div>
                  <div className="ml-4">
                    {setting.component}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default Settings;