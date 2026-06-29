'use client';

import React, { useEffect, useState } from 'react';
import { checkHealth } from '@/lib/api';
import { Cpu } from 'lucide-react';

export const Navbar: React.FC = () => {
  const [healthy, setHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    checkHealth()
      .then(() => setHealthy(true))
      .catch(() => setHealthy(false));
  }, []);

  return (
    <nav className="h-16 border-b border-neutral-800/80 bg-neutral-950/70 px-6 flex items-center justify-between backdrop-blur-xl sticky top-0 z-50">
      <div className="flex items-center space-x-3">
        <Cpu className="w-5 h-5 text-indigo-400" />
        <span className="text-md font-bold tracking-wider text-neutral-100">
          CandidateCore
        </span>
        <span className="text-[10px] bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-full font-bold">
          Engine Active
        </span>
      </div>
      <div className="flex items-center space-x-2">
        <div className="flex items-center space-x-2 bg-neutral-900/60 border border-neutral-800 px-3 py-1 rounded-full">
          {healthy === null ? (
            <div className="w-2 h-2 bg-neutral-600 rounded-full animate-pulse" />
          ) : healthy ? (
            <>
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-sm shadow-emerald-500/50" />
              <span className="text-[11px] font-semibold text-neutral-300">API Connected</span>
            </>
          ) : (
            <>
              <div className="w-2 h-2 bg-rose-500 rounded-full shadow-sm shadow-rose-500/50" />
              <span className="text-[11px] font-semibold text-rose-400">Disconnected</span>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};
export default Navbar;
