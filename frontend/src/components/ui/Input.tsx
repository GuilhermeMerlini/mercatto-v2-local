import { InputHTMLAttributes, forwardRef, useId } from "react";
import "./Input.css";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, ...props }, ref) => {
    const id = useId();
    const errorId = error ? `${id}-error` : undefined;

    return (
      <div className="input-wrapper">
        <label htmlFor={id} className="input-label">
          {label}
        </label>
        <input
          {...props}
          ref={ref}
          id={id}
          className={`input${error ? " input--error" : ""}${className ? ` ${className}` : ""}`}
          aria-invalid={error ? true : undefined}
          aria-describedby={errorId}
        />
        {error && (
          <div id={errorId} className="input-error">
            {error}
          </div>
        )}
      </div>
    );
  }
);
