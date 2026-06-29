import React from 'react';

export const Loading: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center py-10 px-4 space-y-4 text-center">
      <div className="relative w-12 h-12">
        {/* Outer pulse */}
        <div className="absolute inset-0 rounded-full border-4 border-indigo-500/20 animate-ping" />
        {/* Inner rotating gradient indicator */}
        <div className="w-12 h-12 rounded-full border-4 border-transparent border-t-indigo-500 border-r-violet-400 animate-spin" />
      </div>
      <div className="space-y-1">
        <h4 className="text-sm font-semibold text-neutral-200 tracking-wide">Processing Pipeline</h4>
        <p className="text-xs text-neutral-400">Analyzing, parsing, and resolving identity profiles...</p>
      </div>
    </div>
  );
};
