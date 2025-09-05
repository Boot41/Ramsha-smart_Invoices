import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Bot,
  FileSignature,
  Store,
  Users,
  Settings,
  ChevronDown,
  Zap
} from 'lucide-react';
import { cn } from '../../lib/utils';

interface SidebarProps {
  isOpen: boolean;
  toggleSidebar: () => void;
}

interface MenuItemType {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  path: string;
  children?: Array<{
    id: string;
    label: string;
    path: string;
  }>;
}

const menuItems: MenuItemType[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: LayoutDashboard,
    path: '/dashboard'
  },
  {
    id: 'invoices',
    label: 'Invoices',
    icon: FileText,
    path: '/invoices',
    children: [
      { id: 'all-invoices', label: 'All Invoices', path: '/invoices' },
      { id: 'invoice-templates', label: 'Templates', path: '/invoices/templates' },
      { id: 'invoice-scheduling', label: 'Scheduling', path: '/invoices/scheduling' }
    ]
  },
  {
    id: 'contracts',
    label: 'Contracts',
    icon: FileSignature,
    path: '/contracts'
  },

  // {
  //   id: 'admin',
  //   label: 'Admin',
  //   icon: Users,
  //   path: '/admin',
  //   children: [
  //     { id: 'admin-dashboard', label: 'Admin Dashboard', path: '/admin' },
  //     { id: 'user-management', label: 'Users', path: '/admin/users' },
  //     { id: 'enterprise-signup', label: 'Enterprise Signup', path: '/auth/enterprise-signup' }
  //   ]
  // }
];

const Sidebar: React.FC<SidebarProps> = ({ isOpen, toggleSidebar }) => {
  const location = useLocation();
  const [expandedItems, setExpandedItems] = React.useState<string[]>(['invoices']);

  const toggleExpanded = (itemId: string) => {
    setExpandedItems(prev =>
      prev.includes(itemId)
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const isActive = (path: string) => {
    return location.pathname === path || 
           (path !== '/' && location.pathname.startsWith(path));
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-gray-600 bg-opacity-75 lg:hidden z-20"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar */}
      <div
        className={cn(
          'fixed inset-y-0 left-0 z-30 w-64 bg-gray-900 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-center px-4 py-6 border-b border-gray-700">
            <h1 className="text-xl font-bold text-white">Smart Invoice</h1>
          </div>

          <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
            {menuItems.map((item) => (
              <div key={item.id}>
                {item.children ? (
                  <div>
                    <button
                      onClick={() => toggleExpanded(item.id)}
                      className={cn(
                        'w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors duration-200',
                        isActive(item.path)
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                      )}
                    >
                      <item.icon className="w-5 h-5 mr-3" />
                      <span className="flex-1 text-left">{item.label}</span>
                      <ChevronDown
                        className={cn(
                          'w-4 h-4 transition-transform duration-200',
                          expandedItems.includes(item.id) ? 'rotate-180' : ''
                        )}
                      />
                    </button>
                    
                    {expandedItems.includes(item.id) && (
                      <div className="ml-6 mt-2 space-y-1">
                        {item.children.map((child) => (
                          <Link
                            key={child.id}
                            to={child.path}
                            className={cn(
                              'block px-3 py-2 text-sm rounded-lg transition-colors duration-200',
                              isActive(child.path)
                                ? 'bg-blue-600 text-white'
                                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                            )}
                          >
                            {child.label}
                          </Link>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <Link
                    to={item.path}
                    className={cn(
                      'flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors duration-200',
                      isActive(item.path)
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                    )}
                  >
                    <item.icon className="w-5 h-5 mr-3" />
                    {item.label}
                  </Link>
                )}
              </div>
            ))}
          </nav>

          <div className="p-4 border-t border-gray-700">
            <Link
              to="/settings"
              className="flex items-center px-3 py-2 text-sm font-medium text-gray-300 rounded-lg hover:bg-gray-800 hover:text-white transition-colors duration-200"
            >
              <Settings className="w-5 h-5 mr-3" />
              Settings
            </Link>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;