import React from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className = '', label, error, hint, type = 'text', ...props }, ref) => {
    const baseClasses = 'flex h-10 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-base placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-all duration-200 hover:border-indigo-300 focus:border-indigo-500 focus:shadow-sm focus:shadow-indigo-500/10';
    
    const errorClasses = error ? 'border-red-500 focus-visible:ring-red-500 focus:shadow-red-500/10' : '';
    
    const classes = [baseClasses, errorClasses, className].filter(Boolean).join(' ');

    return (
      <div className="space-y-2">
        {label && (
          <label className="text-sm font-medium text-foreground">
            {label}
          </label>
        )}
        <input
          type={type}
          className={classes}
          ref={ref}
          {...props}
        />
        {error && (
          <p className="text-sm text-error-600">
            {error}
          </p>
        )}
        {hint && !error && (
          <p className="text-sm text-muted-foreground">
            {hint}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export { Input };