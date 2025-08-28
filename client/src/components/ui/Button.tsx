import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'purple' | 'orange' | 'outline' | 'ghost' | 'link' | 'gradient';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  fullWidth?: boolean;
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'full';
  shadow?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ 
    className = '', 
    variant = 'primary', 
    size = 'md', 
    fullWidth = false, 
    loading = false, 
    disabled, 
    children, 
    leftIcon,
    rightIcon,
    rounded = 'md',
    shadow = 'none',
    ...props 
  }, ref) => {
    const baseClasses = 'inline-flex items-center justify-center font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed';

    const variants = {
      primary: 'bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800 hover:shadow-lg hover:shadow-blue-600/25 transition-all duration-200 font-medium',
      secondary: 'bg-slate-100 text-slate-700 hover:bg-slate-200 active:bg-slate-300 border border-slate-200 hover:border-slate-300 transition-all duration-200',
      success: 'bg-green-600 text-white hover:bg-green-700 active:bg-green-800 hover:shadow-lg hover:shadow-green-600/25 transition-all duration-200 font-medium',
      warning: 'bg-amber-500 text-white hover:bg-amber-600 active:bg-amber-700 hover:shadow-lg hover:shadow-amber-500/25 transition-all duration-200 font-medium',
      error: 'bg-red-600 text-white hover:bg-red-700 active:bg-red-800 hover:shadow-lg hover:shadow-red-600/25 transition-all duration-200 font-medium',
      info: 'bg-cyan-600 text-white hover:bg-cyan-700 active:bg-cyan-800 hover:shadow-lg hover:shadow-cyan-600/25 transition-all duration-200 font-medium',
      purple: 'bg-purple-600 text-white hover:bg-purple-700 active:bg-purple-800 hover:shadow-lg hover:shadow-purple-600/25 transition-all duration-200 font-medium',
      orange: 'bg-orange-600 text-white hover:bg-orange-700 active:bg-orange-800 hover:shadow-lg hover:shadow-orange-600/25 transition-all duration-200 font-medium',
      outline: 'border-2 border-blue-600 bg-white text-blue-600 hover:bg-blue-50 hover:text-blue-700 active:bg-blue-100 transition-all duration-200',
      ghost: 'text-slate-600 hover:bg-slate-100 hover:text-slate-700 active:bg-slate-200 transition-all duration-200',
      link: 'text-blue-600 underline-offset-4 hover:underline hover:text-blue-700 active:text-blue-800 transition-all duration-200 font-medium',
      gradient: 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 hover:shadow-lg transition-all duration-200 font-medium',
    };

    const sizes = {
      xs: 'h-7 px-2.5 text-xs gap-1',
      sm: 'h-8 px-3 text-sm gap-1.5',
      md: 'h-10 px-4 text-base gap-2',
      lg: 'h-12 px-6 text-lg gap-2.5',
      xl: 'h-14 px-8 text-xl gap-3',
    };

    const roundedClasses = {
      none: 'rounded-none',
      sm: 'rounded-sm',
      md: 'rounded-lg',
      lg: 'rounded-xl',
      full: 'rounded-full',
    };

    const shadowClasses = {
      none: '',
      sm: 'shadow-sm',
      md: 'shadow-md',
      lg: 'shadow-lg',
      xl: 'shadow-xl',
    };

    const classes = [
      baseClasses,
      variants[variant],
      sizes[size],
      roundedClasses[rounded],
      shadowClasses[shadow],
      fullWidth ? 'w-full' : '',
      className,
    ].filter(Boolean).join(' ');

    const iconSize = {
      xs: 'h-3 w-3',
      sm: 'h-3.5 w-3.5',
      md: 'h-4 w-4',
      lg: 'h-5 w-5',
      xl: 'h-6 w-6',
    }[size];

    const spinnerSize = {
      xs: 'h-3 w-3',
      sm: 'h-3.5 w-3.5', 
      md: 'h-4 w-4',
      lg: 'h-5 w-5',
      xl: 'h-6 w-6',
    }[size];

    return (
      <button
        className={classes}
        disabled={disabled || loading}
        ref={ref}
        {...props}
      >
        {loading ? (
          <svg className={`animate-spin ${spinnerSize}`} fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        ) : leftIcon && (
          <span className={iconSize}>{leftIcon}</span>
        )}
        
        {children}
        
        {!loading && rightIcon && (
          <span className={iconSize}>{rightIcon}</span>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

export { Button };