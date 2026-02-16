import { cn } from "@/lib/utils";
import { HTMLAttributes, forwardRef } from "react";

export type SkeletonVariant = "text" | "circle" | "card" | "inline";

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: SkeletonVariant;
  width?: string | number;
  height?: string | number;
}

const variantStyles: Record<SkeletonVariant, string> = {
  text: "h-4 w-full rounded",
  circle: "rounded-full aspect-square",
  card: "h-32 w-full rounded-sara",
  inline: "h-4 w-24 rounded inline-block",
};

export const Skeleton = forwardRef<HTMLDivElement, SkeletonProps>(
  ({ variant = "text", width, height, className, style, ...props }, ref) => {
    const customStyle = {
      ...style,
      ...(width !== undefined && {
        width: typeof width === "number" ? `${width}px` : width,
      }),
      ...(height !== undefined && {
        height: typeof height === "number" ? `${height}px` : height,
      }),
    };

    return (
      <div
        ref={ref}
        className={cn(
          "bg-sara-bg-subtle animate-pulse",
          variantStyles[variant],
          className
        )}
        style={customStyle}
        {...props}
      />
    );
  }
);

Skeleton.displayName = "Skeleton";

export interface SkeletonTextProps extends HTMLAttributes<HTMLDivElement> {
  lines?: number;
  lastLineWidth?: string;
}

export const SkeletonText = forwardRef<HTMLDivElement, SkeletonTextProps>(
  ({ lines = 3, lastLineWidth = "75%", className, ...props }, ref) => {
    return (
      <div ref={ref} className={cn("space-y-2", className)} {...props}>
        {Array.from({ length: lines }).map((_, index) => (
          <Skeleton
            key={index}
            variant="text"
            width={index === lines - 1 ? lastLineWidth : "100%"}
          />
        ))}
      </div>
    );
  }
);

SkeletonText.displayName = "SkeletonText";

export interface SkeletonCardProps extends HTMLAttributes<HTMLDivElement> {
  hasHeader?: boolean;
  hasFooter?: boolean;
}

export const SkeletonCard = forwardRef<HTMLDivElement, SkeletonCardProps>(
  ({ hasHeader = true, hasFooter = false, className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "bg-sara-bg-surface rounded-sara p-4 space-y-4",
          className
        )}
        {...props}
      >
        {hasHeader && (
          <div className="flex items-center gap-3">
            <Skeleton variant="circle" width={40} height={40} />
            <div className="flex-1 space-y-2">
              <Skeleton variant="text" width="60%" />
              <Skeleton variant="text" width="40%" />
            </div>
          </div>
        )}
        <SkeletonText lines={3} />
        {hasFooter && (
          <div className="flex gap-2 pt-2">
            <Skeleton variant="inline" width={80} height={32} />
            <Skeleton variant="inline" width={80} height={32} />
          </div>
        )}
      </div>
    );
  }
);

SkeletonCard.displayName = "SkeletonCard";

export default Skeleton;
