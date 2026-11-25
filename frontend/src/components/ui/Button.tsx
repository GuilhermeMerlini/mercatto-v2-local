import { ButtonHTMLAttributes, forwardRef } from "react";
import "./Button.css";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", loading = false, disabled, className, children, ...props }, ref) => {
    const classes = `btn btn--${variant}${loading ? " btn--loading" : ""}${className ? ` ${className}` : ""}`;
    
    return (
      <button
        {...props}
        ref={ref}
        className={classes}
        disabled={disabled || loading}
        aria-busy={loading || undefined}
      >
        {children}
      </button>
    );
  }
);
