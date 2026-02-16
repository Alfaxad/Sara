"use client";

import { TASKS } from "@/lib/tasks";
import { TaskCard } from "./TaskCard";
import { cn } from "@/lib/utils";

export interface TaskGridProps {
  className?: string;
}

export function TaskGrid({ className }: TaskGridProps) {
  return (
    <section className={cn("w-full px-5", className)}>
      <div className="max-w-[840px] mx-auto">
        {/* Divider + Section Header */}
        <div className="border-t border-sara-border mb-9">
          <div className="pt-6">
            <h2 className="text-heading text-sara-text-primary mb-1.5">
              Clinical Workflows
            </h2>
            <p className="text-body-small text-sara-text-muted">
              Select a task to start a conversation with Sara
            </p>
          </div>
        </div>

        {/* Grid - Responsive 2 columns */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {TASKS.map((task, index) => (
            <TaskCard key={task.id} task={task} index={index} />
          ))}
        </div>
      </div>
    </section>
  );
}

export default TaskGrid;
