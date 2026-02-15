"use client";

import { AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

export interface DisclaimerProps {
  className?: string;
}

export function Disclaimer({ className }: DisclaimerProps) {
  return (
    <section className={cn("w-full px-4 py-8", className)}>
      <div className="max-w-4xl mx-auto">
        <div className="flex items-start gap-4 p-4 rounded-sara bg-sara-warning-soft border border-sara-warning/30">
          {/* Warning Icon */}
          <div className="flex-shrink-0">
            <AlertTriangle className="w-5 h-5 text-sara-warning" />
          </div>

          {/* Disclaimer Text */}
          <div className="flex-1">
            <h3 className="font-body text-subheading text-sara-warning mb-1">
              Research Demo Only
            </h3>
            <p className="text-body-small text-sara-text-secondary">
              Sara is a research demonstration and should not be used for actual
              clinical decision-making. This tool is intended for evaluation and
              research purposes only. Always consult qualified healthcare
              professionals for medical advice and treatment decisions.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

export default Disclaimer;
