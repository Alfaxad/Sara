"use client";

import { cn } from "@/lib/utils";

export interface HeroProps {
  className?: string;
}

export function Hero({ className }: HeroProps) {
  return (
    <section
      className={cn(
        "flex flex-col items-center justify-center text-center pt-8 pb-8 px-5",
        "animate-fade-up",
        className
      )}
    >
      {/* Logo - White circle with S */}
      <div className="mb-4">
        <div className="sara-avatar">S</div>
      </div>

      {/* Title */}
      <h1 className="text-display-xl text-sara-text-primary mb-0">Sara</h1>

      {/* Subtitle */}
      <div className="text-body text-sara-text-muted mt-3 tracking-tight">
        Clinical Workflow Agent
      </div>

      {/* Description */}
      <p className="text-body text-sara-text-secondary mt-4 max-w-[480px] leading-relaxed">
        An intelligent agent that assists healthcare professionals in managing
        clinical workflows, patient data, and medical documentation.
      </p>
    </section>
  );
}

export default Hero;
