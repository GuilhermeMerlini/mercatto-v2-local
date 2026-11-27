import { InputHTMLAttributes, forwardRef, useId } from "react";
import "./Input.css";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  /** Dica fixa abaixo do campo (ex.: regra da senha). O erro, quando há, substitui a dica na descrição acessível. */
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, className, ...props }, ref) => {
    const id = useId();
    const errorId = error ? `${id}-error` : undefined;
    const hintId = hint ? `${id}-hint` : undefined;

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
          aria-describedby={errorId ?? hintId}
        />
        {hint && (
          <div id={hintId} className="input-hint">
            {hint}
          </div>
        )}
        {error && (
          <div id={errorId} className="input-error">
            {error}
          </div>
        )}
      </div>
    );
  }
);
