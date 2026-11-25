import { ReactNode } from "react";
import "./ErrorMessage.css";

interface ErrorMessageProps {
  children: ReactNode;
}

export function ErrorMessage({ children }: ErrorMessageProps) {
  return (
    <div role="alert" className="error-message">
      {children}
    </div>
  );
}
