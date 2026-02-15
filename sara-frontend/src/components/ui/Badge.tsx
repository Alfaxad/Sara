import { cn } from "@/lib/utils";
import { HTMLAttributes, forwardRef } from "react";

export type BadgeVariant =
  | "default"
  | "info"
  | "success"
  | "warning"
  | "critical"
  | "accent";

export type BadgeSize = "sm" | "md";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: BadgeSize;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: "bg-sara-bg-subtle text-sara-text-secondary",
  info: "bg-sara-info-soft text-sara-info",
  success: "bg-sara-success-soft text-sara-success",
  warning: "bg-sara-warning-soft text-sara-warning",
  critical: "bg-sara-critical-soft text-sara-critical",
  accent: "bg-sara-accent-soft text-sara-accent",
};

const sizeStyles: Record<BadgeSize, string> = {
  sm: "px-2 py-0.5 text-caption",
  md: "px-3 py-1 text-body-small",
};

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ variant = "default", size = "md", className, children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center font-medium rounded-full",
          "transition-colors duration-150",
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {children}
      </span>
    );
  }
);

Badge.displayName = "Badge";

export default Badge;
