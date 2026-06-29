import React from 'react';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import ErrorBoundary from '../common/ErrorBoundary';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen flex flex-col bg-neutral-950 text-neutral-200 font-sans selection:bg-indigo-500/35">
      <Navbar />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-6 md:p-8 overflow-y-auto">
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
};
export default Layout;
