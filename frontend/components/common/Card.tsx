import React from 'react';
import { cn } from '@/lib/utils';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  description?: string;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, title, description, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "rounded-2xl border border-neutral-800 bg-neutral-900/40 p-6 shadow-2xl backdrop-blur-xl transition-all duration-300 hover:border-neutral-700/60 hover:shadow-neutral-950/40",
          className
        )}
        {...props}
      >
        {(title || description) && (
          <div className="mb-5 border-b border-neutral-800/60 pb-4">
            {title && (
              <h3 className="text-lg font-bold tracking-tight text-neutral-100">
                {title}
              </h3>
            )}
            {description && (
              <p className="mt-1 text-xs text-neutral-400">
                {description}
              </p>
            )}
          </div>
        )}
        <div className="text-sm text-neutral-300">
          {children}
        </div>
      </div>
    );
  }
);

Card.displayName = 'Card';
