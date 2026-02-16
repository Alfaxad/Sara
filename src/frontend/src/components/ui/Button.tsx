import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes, forwardRef, ReactNode } from "react";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: cn(
    "bg-sara-accent text-white",
    "hover:bg-sara-accent-hover",
    "focus:ring-2 focus:ring-sara-accent focus:ring-offset-2 focus:ring-offset-sara-bg-base",
    "disabled:bg-sara-accent/50 disabled:cursor-not-allowed"
  ),
  secondary: cn(
    "bg-transparent border border-sara-border text-sara-text-primary",
    "hover:bg-sara-bg-subtle hover:border-sara-border-focus",
    "focus:ring-2 focus:ring-sara-accent focus:ring-offset-2 focus:ring-offset-sara-bg-base",
    "disabled:opacity-50 disabled:cursor-not-allowed"
  ),
  ghost: cn(
    "bg-transparent text-sara-text-secondary",
    "hover:bg-sara-bg-subtle hover:text-sara-text-primary",
    "focus:ring-2 focus:ring-sara-accent focus:ring-offset-2 focus:ring-offset-sara-bg-base",
    "disabled:opacity-50 disabled:cursor-not-allowed"
  ),
  danger: cn(
    "bg-sara-critical text-white",
    "hover:bg-sara-critical/90",
    "focus:ring-2 focus:ring-sara-critical focus:ring-offset-2 focus:ring-offset-sara-bg-base",
    "disabled:bg-sara-critical/50 disabled:cursor-not-allowed"
  ),
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-body-small gap-1.5",
  md: "px-4 py-2 text-body gap-2",
  lg: "px-6 py-3 text-body gap-2.5",
};

const iconSizeStyles: Record<ButtonSize, string> = {
  sm: "w-4 h-4",
  md: "w-5 h-5",
  lg: "w-5 h-5",
};

const LoadingSpinner = ({ size }: { size: ButtonSize }) => (
  <svg
    className={cn("animate-sara-spin", iconSizeStyles[size])}
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
  >
    <circle
      className="opacity-25"
      cx="12"
      cy="12"
      r="10"
      stroke="currentColor"
      strokeWidth="4"
    />
    <path
      className="opacity-75"
      fill="currentColor"
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
    />
  </svg>
);

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      isLoading = false,
      leftIcon,
      rightIcon,
      disabled,
      className,
      children,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || isLoading;

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        className={cn(
          "inline-flex items-center justify-center font-medium",
          "rounded-sara-sm",
          "transition-colors duration-150",
          "focus:outline-none",
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {isLoading ? (
          <LoadingSpinner size={size} />
        ) : leftIcon ? (
          <span className={iconSizeStyles[size]}>{leftIcon}</span>
        ) : null}
        {children}
        {!isLoading && rightIcon && (
          <span className={iconSizeStyles[size]}>{rightIcon}</span>
        )}
      </button>
    );
  }
);

Button.displayName = "Button";

export default Button;
