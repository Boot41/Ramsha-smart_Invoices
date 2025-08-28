import React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'outline' | 'info' | 'purple' | 'orange';
  size?: 'sm' | 'md' | 'lg';
}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className = '', variant = 'primary', size = 'md', children, ...props }, ref) => {
    const baseClasses = 'inline-flex items-center rounded-full font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 hover:scale-105 active:scale-100 cursor-pointer'

    const variants = {
      primary: 'bg-blue-100 text-blue-800 border border-blue-200 hover:bg-blue-200 hover:text-blue-900 transition-all duration-200 font-medium',
      secondary: 'bg-slate-100 text-slate-700 border border-slate-200 hover:bg-slate-200 hover:text-slate-800 transition-all duration-200',
      success: 'bg-green-100 text-green-800 border border-green-200 hover:bg-green-200 hover:text-green-900 transition-all duration-200 font-medium',
      warning: 'bg-amber-100 text-amber-800 border border-amber-200 hover:bg-amber-200 hover:text-amber-900 transition-all duration-200 font-medium',
      error: 'bg-red-100 text-red-800 border border-red-200 hover:bg-red-200 hover:text-red-900 transition-all duration-200 font-medium',
      outline: 'text-blue-600 border border-blue-200 hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300 transition-all duration-200',
      info: 'bg-cyan-100 text-cyan-800 border border-cyan-200 hover:bg-cyan-200 hover:text-cyan-900 transition-all duration-200 font-medium',
      purple: 'bg-purple-100 text-purple-800 border border-purple-200 hover:bg-purple-200 hover:text-purple-900 transition-all duration-200 font-medium',
      orange: 'bg-orange-100 text-orange-800 border border-orange-200 hover:bg-orange-200 hover:text-orange-900 transition-all duration-200 font-medium',
    };

    const sizes = {
      sm: 'px-2.5 py-0.5 text-xs',
      md: 'px-3 py-1 text-sm',
      lg: 'px-4 py-1.5 text-base',
    };

    const classes = [
      baseClasses,
      variants[variant],
      sizes[size],
      className,
    ].filter(Boolean).join(' ');

    return (
      <>
      <div className={classes} ref={ref} {...props}>
        {children}
      </div>
      </>
    );
  }
);

Badge.displayName = 'Badge';

export { Badge };