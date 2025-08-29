import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bell, User, Settings, LogOut, ChevronDown, Palette, Mail, Shield, Moon, Sun } from 'lucide-react';
import { Button } from '../ui';
import { useAuth } from '../../../hooks/useAuth';

interface NavbarProps {
  toggleSidebar: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ toggleSidebar }) => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [showSettingsDropdown, setShowSettingsDropdown] = useState(false);
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const settingsDropdownRef = useRef<HTMLDivElement>(null);
  const userDropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (settingsDropdownRef.current && !settingsDropdownRef.current.contains(event.target as Node)) {
        setShowSettingsDropdown(false);
      }
      if (userDropdownRef.current && !userDropdownRef.current.contains(event.target as Node)) {
        setShowUserDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const settingsQuickActions = [
    {
      icon: Palette,
      label: 'Change Theme',
      description: 'Switch between light and dark mode',
      action: () => console.log('Toggle theme')
    },
    {
      icon: Mail,
      label: 'Email Templates',
      description: 'Customize invoice email templates',
      action: () => console.log('Email templates')
    },
    {
      icon: Bell,
      label: 'Notifications',
      description: 'Configure reminder settings',
      action: () => console.log('Notification settings')
    },
    {
      icon: Shield,
      label: 'Security',
      description: 'Password & 2FA settings',
      action: () => console.log('Security settings')
    }
  ];

  return (
    <header className="bg-white border-b border-gray-200 px-4 py-3 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleSidebar}
            className="lg:hidden mr-2"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </Button>
          <h1 className="text-xl font-semibold text-gray-900">
            Smart Invoice Scheduler
          </h1>
        </div>

        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="sm" className="relative">
            <Bell className="w-5 h-5" />
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
              3
            </span>
          </Button>

          <div className="flex items-center space-x-2">
            {/* Settings Dropdown */}
            <div className="relative" ref={settingsDropdownRef}>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => setShowSettingsDropdown(!showSettingsDropdown)}
                className="flex items-center space-x-1"
              >
                <Settings className="w-5 h-5" />
                <ChevronDown className="w-3 h-3" />
              </Button>

              {showSettingsDropdown && (
                <div className="absolute right-0 mt-2 w-80 bg-white rounded-md shadow-lg border border-gray-200 z-50">
                  <div className="p-3 border-b border-gray-100">
                    <div className="flex items-center justify-between">
                      <h3 className="font-medium text-gray-900">Quick Settings</h3>
                      <Link 
                        to="/settings"
                        className="text-xs text-blue-600 hover:text-blue-700"
                        onClick={() => setShowSettingsDropdown(false)}
                      >
                        View All Settings
                      </Link>
                    </div>
                  </div>
                  
                  <div className="p-2">
                    {settingsQuickActions.map((item, index) => (
                      <button
                        key={index}
                        onClick={() => {
                          item.action();
                          setShowSettingsDropdown(false);
                        }}
                        className="w-full flex items-center space-x-3 p-3 text-left hover:bg-gray-50 rounded-md transition-colors"
                      >
                        <div className="p-2 bg-gray-100 rounded-md">
                          <item.icon className="w-4 h-4 text-gray-600" />
                        </div>
                        <div className="flex-1">
                          <p className="font-medium text-gray-900 text-sm">{item.label}</p>
                          <p className="text-xs text-gray-500">{item.description}</p>
                        </div>
                      </button>
                    ))}
                  </div>

                  <div className="p-3 border-t border-gray-100 bg-gray-50">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Quick Theme Toggle</span>
                      <div className="flex space-x-1">
                        <button className="p-1 hover:bg-gray-200 rounded">
                          <Sun className="w-4 h-4 text-gray-600" />
                        </button>
                        <button className="p-1 hover:bg-gray-200 rounded">
                          <Moon className="w-4 h-4 text-gray-600" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-2 pl-2 border-l border-gray-200">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                <User className="w-5 h-5 text-white" />
              </div>
              <div className="hidden sm:block">
                <p className="text-sm font-medium text-gray-900">{user ? `${user.firstName} ${user.lastName}` : 'User'}</p>
                <p className="text-xs text-gray-500">{user?.role || 'Member'}</p>
              </div>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={async () => {
                  await logout();
                  navigate('/auth/login');
                }}
              >
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar;