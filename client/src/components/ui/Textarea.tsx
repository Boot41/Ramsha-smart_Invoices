import React from 'react';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  hint?: string;
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className = '', label, error, hint, ...props }, ref) => {
    const baseClasses = 'flex min-h-[80px] w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-base placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-y transition-all duration-200 hover:border-indigo-300 focus:border-indigo-500 focus:shadow-sm focus:shadow-indigo-500/10';
    
    const errorClasses = error ? 'border-red-500 focus-visible:ring-red-500 focus:shadow-red-500/10' : '';
    
    const classes = [baseClasses, errorClasses, className].filter(Boolean).join(' ');

    return (
      <div className="space-y-2">
        {label && (
          <label className="text-sm font-medium text-slate-700">
            {label}
          </label>
        )}
        <textarea
          className={classes}
          ref={ref}
          {...props}
        />
        {error && (
          <p className="text-sm text-red-600">
            {error}
          </p>
        )}
        {hint && !error && (
          <p className="text-sm text-slate-500">
            {hint}
          </p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

export { Textarea };