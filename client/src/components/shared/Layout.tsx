import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar, Sidebar } from '.';

const Layout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar isOpen={sidebarOpen} toggleSidebar={toggleSidebar} />
      
      <div className="flex-1 flex flex-col overflow-hidden lg:ml-0">
        <Navbar toggleSidebar={toggleSidebar} />
        
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 p-6">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;