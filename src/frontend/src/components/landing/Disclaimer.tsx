"use client";

import { AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

export interface DisclaimerProps {
  className?: string;
}

export function Disclaimer({ className }: DisclaimerProps) {
  return (
    <section className={cn("w-full px-5 py-12", className)}>
      <div className="max-w-[840px] mx-auto">
        <div className="border-t border-sara-border pt-6">
          <div className="flex items-start gap-3">
            {/* Warning Icon */}
            <div className="flex-shrink-0 mt-0.5">
              <AlertTriangle className="w-4 h-4 text-sara-text-muted" />
            </div>

            {/* Disclaimer Text */}
            <div className="flex-1">
              <h3 className="text-body-small font-medium text-sara-text-secondary mb-2">
                Disclaimer
              </h3>
              <p className="text-caption text-sara-text-muted leading-relaxed">
                This demonstration is for illustrative purposes only and does not
                represent a finished or approved product. It is not representative
                of compliance to any regulations or standards for quality, safety
                or efficacy. Any real-world application would require additional
                development, training, and adaptation. The experience highlighted
                in this demo shows Sara&apos;s capability for the displayed task and is
                intended to help developers and users explore possible applications
                and inspire further development. Demo data obtained from MedAgentBench.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default Disclaimer;
