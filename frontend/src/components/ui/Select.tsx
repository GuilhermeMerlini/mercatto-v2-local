import { SelectHTMLAttributes, forwardRef, useId } from "react";
import "./Select.css";

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  error?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, children, className, ...props }, ref) => {
    const id = useId();
    const errorId = error ? `${id}-error` : undefined;

    return (
      <div className="select-wrapper">
        <label htmlFor={id} className="select-label">
          {label}
        </label>
        <select
          {...props}
          ref={ref}
          id={id}
          className={`select${error ? " select--error" : ""}${className ? ` ${className}` : ""}`}
          aria-invalid={error ? true : undefined}
          aria-describedby={errorId}
        >
          {children}
        </select>
        {error && (
          <div id={errorId} className="select-error">
            {error}
          </div>
        )}
      </div>
    );
  }
);
