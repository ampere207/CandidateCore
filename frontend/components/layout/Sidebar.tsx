'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Layers, Database, Settings, RefreshCw } from 'lucide-react';

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  const links = [
    { name: 'Canonicalization Run', href: '/', icon: RefreshCw },
    { name: 'Identity Resolution', href: '#', icon: Layers, disabled: true },
    { name: 'Lineage Explainability', href: '#', icon: Database, disabled: true },
    { name: 'Target Projections', href: '#', icon: Settings, disabled: true }
  ];

  return (
    <aside className="w-64 border-r border-neutral-800/80 bg-neutral-950/20 p-4 space-y-6 flex-shrink-0 hidden md:block">
      <div className="px-3">
        <h3 className="text-[10px] font-bold tracking-widest text-neutral-500 uppercase">
          Pipeline Control
        </h3>
      </div>
      <nav className="space-y-1.5">
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = pathname === link.href;
          
          if (link.disabled) {
            return (
              <div
                key={link.name}
                className="flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium text-neutral-600 cursor-not-allowed select-none"
              >
                <div className="flex items-center space-x-3">
                  <Icon className="w-4 h-4" />
                  <span>{link.name}</span>
                </div>
                <span className="text-[9px] bg-neutral-900 border border-neutral-800 text-neutral-500 px-1.5 py-0.5 rounded-md">
                  Phase 2
                </span>
              </div>
            );
          }

          return (
            <Link
              key={link.name}
              href={link.href}
              className={cn(
                "flex items-center space-x-3 px-3 py-2.5 rounded-xl text-sm font-medium transition duration-200",
                isActive
                  ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/25"
                  : "text-neutral-400 hover:bg-neutral-900/50 hover:text-neutral-200"
              )}
            >
              <Icon className="w-4 h-4" />
              <span>{link.name}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
};
export default Sidebar;
