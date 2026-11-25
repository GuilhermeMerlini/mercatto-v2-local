import { ComponentPropsWithoutRef, forwardRef } from "react";
import "./Card.css";

export interface CardProps extends ComponentPropsWithoutRef<"div"> {
  as?: "div" | "article" | "section";
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ as: Component = "div", className, children, ...props }, ref) => {
    return (
      <Component {...props} ref={ref} className={`card${className ? ` ${className}` : ""}`}>
        {children}
      </Component>
    );
  }
);
