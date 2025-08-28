import React from 'react';

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'onChange'> {
  label?: string;
  error?: string;
  hint?: string;
  options: SelectOption[];
  placeholder?: string;
  onChange?: (value: string) => void;
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className = '', label, error, hint, options, placeholder, onChange, value, ...props }, ref) => {
    const baseClasses = 'flex h-10 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 appearance-none bg-no-repeat bg-right pr-8 transition-all duration-200 hover:border-indigo-300 focus:border-indigo-500 focus:shadow-sm focus:shadow-indigo-500/10';
    
    const errorClasses = error ? 'border-red-500 focus-visible:ring-red-500 focus:shadow-red-500/10' : '';
    
    const classes = [baseClasses, errorClasses, className].filter(Boolean).join(' ');

    const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
      if (onChange) {
        onChange(e.target.value);
      }
    };

    return (
      <div className="space-y-2">
        {label && (
          <label className="text-sm font-medium text-foreground">
            {label}
          </label>
        )}
        <div className="relative">
          <select
            className={classes}
            ref={ref}
            value={value}
            onChange={handleChange}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map((option) => (
              <option key={option.value} value={option.value} disabled={option.disabled}>
                {option.label}
              </option>
            ))}
          </select>
          <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
            <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
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

Select.displayName = 'Select';

export { Select };