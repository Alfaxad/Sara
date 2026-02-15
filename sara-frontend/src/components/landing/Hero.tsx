"use client";

import { cn } from "@/lib/utils";

export interface HeroProps {
  className?: string;
}

export function Hero({ className }: HeroProps) {
  return (
    <section
      className={cn(
        "flex flex-col items-center justify-center text-center py-16 px-4",
        className
      )}
    >
      {/* Logo with pulse animation */}
      <div className="relative mb-6">
        <div className="w-20 h-20 rounded-full bg-sara-accent-soft flex items-center justify-center animate-sara-pulse">
          <span className="text-4xl font-display text-sara-accent font-bold">
            S
          </span>
        </div>
      </div>

      {/* Title with Playfair Display */}
      <h1 className="font-display text-display-xl text-sara-text-primary mb-2">
        Sara
      </h1>

      {/* Tagline */}
      <p className="text-heading text-sara-accent mb-4">
        Clinical Workflow Agent
      </p>

      {/* Description */}
      <p className="text-body text-sara-text-secondary max-w-md">
        An intelligent assistant that helps healthcare professionals manage
        clinical workflows, patient data, and medical documentation with ease.
      </p>
    </section>
  );
}

export default Hero;
