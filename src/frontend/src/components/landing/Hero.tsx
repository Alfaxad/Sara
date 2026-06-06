"use client";

import { cn } from "@/lib/utils";

export interface HeroProps {
  className?: string;
}

export function Hero({ className }: HeroProps) {
  const capabilities = ["IRIS FHIR R4", "Interop trace", "Sara 1.5 4B"];

  return (
    <section
      className={cn(
        "flex flex-col items-center justify-center text-center pt-7 pb-8 px-5",
        "animate-fade-up",
        className
      )}
    >
      <div className="mb-4">
        <div className="sara-avatar">S</div>
      </div>

      <h1 className="text-display-xl text-sara-text-primary mb-0">Sara</h1>

      <div className="text-body text-sara-text-muted mt-3">
        Clinical Workflow Agent
      </div>

      <p className="text-body text-sara-text-secondary mt-4 max-w-[560px] leading-relaxed">
        An intelligent agent that assists healthcare professionals in managing
        clinical workflows, patient data, and medical documentation.
      </p>

      <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
        {capabilities.map((capability) => (
          <span key={capability} className="sara-capability">
            <span className="sara-capability-dot" />
            {capability}
          </span>
        ))}
      </div>
    </section>
  );
}

export default Hero;
