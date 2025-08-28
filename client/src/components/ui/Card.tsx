import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  shadow?: 'none' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';
  rounded?: 'sm' | 'md' | 'lg' | 'xl';
  hover?: boolean;
  glass?: boolean;
  gradient?: boolean;
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className = '', padding = 'md', shadow = 'md', rounded = 'lg', hover = false, glass = false, gradient = false, children, ...props }, ref) => {
    const baseClasses = 'bg-card text-card-foreground border border-border transition-all duration-300 ease-out hover:cursor-pointer';
    
    const paddings = {
      none: '',
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
      xl: 'p-10',
    };
    
    const shadows = {
      none: '',
      sm: 'shadow-sm',
      md: 'shadow-md',
      lg: 'shadow-lg',
      xl: 'shadow-xl',
      '2xl': 'shadow-2xl',
    };

    const roundedClasses = {
      sm: 'rounded-sm',
      md: 'rounded-md',
      lg: 'rounded-lg',
      xl: 'rounded-xl',
    };

    const hoverEffects = hover ? 'hover:shadow-xl hover:shadow-black/10 hover:-translate-y-2 hover:scale-[1.02] hover:border-border/80' : '';
    const glassEffect = glass ? 'glass-effect' : '';
    const gradientEffect = gradient ? 'bg-gradient-to-br from-card via-card to-accent/5' : '';

    const classes = [
      baseClasses,
      paddings[padding],
      shadows[shadow],
      roundedClasses[rounded],
      hoverEffects,
      glassEffect,
      gradientEffect,
      className,
    ].filter(Boolean).join(' ');

    return (
      <div className={classes} ref={ref} {...props}>
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

export type CardHeaderProps = React.HTMLAttributes<HTMLDivElement>;

const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className = '', ...props }, ref) => (
    <div
      ref={ref}
      className={`pb-4 ${className}`}
      {...props}
    />
  )
);
CardHeader.displayName = 'CardHeader';

export type CardTitleProps = React.HTMLAttributes<HTMLHeadingElement>;

const CardTitle = React.forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ className = '', ...props }, ref) => (
    <h3
      ref={ref}
      className={`text-2xl font-semibold leading-none tracking-tight ${className}`}
      {...props}
    />
  )
);
CardTitle.displayName = 'CardTitle';

export type CardDescriptionProps = React.HTMLAttributes<HTMLParagraphElement>;

const CardDescription = React.forwardRef<HTMLParagraphElement, CardDescriptionProps>(
  ({ className = '', ...props }, ref) => (
    <p
      ref={ref}
      className={`text-muted-foreground ${className}`}
      {...props}
    />
  )
);
CardDescription.displayName = 'CardDescription';

export type CardContentProps = React.HTMLAttributes<HTMLDivElement>;

const CardContent = React.forwardRef<HTMLDivElement, CardContentProps>(
  ({ className = '', ...props }, ref) => (
    <div ref={ref} className={className} {...props} />
  )
);
CardContent.displayName = 'CardContent';

export type CardFooterProps = React.HTMLAttributes<HTMLDivElement>;

const CardFooter = React.forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className = '', ...props }, ref) => (
    <div
      ref={ref}
      className={`pt-4 flex items-center ${className}`}
      {...props}
    />
  )
);
CardFooter.displayName = 'CardFooter';

export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter };