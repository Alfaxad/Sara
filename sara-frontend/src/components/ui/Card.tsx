import { cn } from "@/lib/utils";
import { ElementType, HTMLAttributes, forwardRef } from "react";

export type CardVariant = "surface" | "elevated" | "outline";

export interface CardProps extends HTMLAttributes<HTMLElement> {
  variant?: CardVariant;
  as?: ElementType;
}

const variantStyles: Record<CardVariant, string> = {
  surface: "bg-sara-bg-surface",
  elevated: "bg-sara-bg-elevated shadow-sara-elevated",
  outline: "bg-transparent border border-sara-border",
};

export const Card = forwardRef<HTMLElement, CardProps>(
  ({ variant = "surface", as: Component = "div", className, children, ...props }, ref) => {
    return (
      <Component
        ref={ref}
        className={cn(
          "rounded-sara p-4",
          variantStyles[variant],
          "transition-colors duration-150",
          className
        )}
        {...props}
      >
        {children}
      </Component>
    );
  }
);

Card.displayName = "Card";

export type CardHeaderProps = HTMLAttributes<HTMLDivElement>;

export const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("mb-4 pb-4 border-b border-sara-border", className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

CardHeader.displayName = "CardHeader";

export type CardTitleProps = HTMLAttributes<HTMLHeadingElement>;

export const CardTitle = forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <h3
        ref={ref}
        className={cn(
          "font-display text-heading text-sara-text-primary",
          className
        )}
        {...props}
      >
        {children}
      </h3>
    );
  }
);

CardTitle.displayName = "CardTitle";

export type CardContentProps = HTMLAttributes<HTMLDivElement>;

export const CardContent = forwardRef<HTMLDivElement, CardContentProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("text-body text-sara-text-secondary", className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

CardContent.displayName = "CardContent";

export type CardFooterProps = HTMLAttributes<HTMLDivElement>;

export const CardFooter = forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "mt-4 pt-4 border-t border-sara-border flex items-center gap-2",
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

CardFooter.displayName = "CardFooter";

export default Card;
