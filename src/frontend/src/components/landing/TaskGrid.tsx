"use client";

import { TASKS } from "@/lib/tasks";
import { TaskCard } from "./TaskCard";
import { cn } from "@/lib/utils";

export interface TaskGridProps {
  className?: string;
}

export function TaskGrid({ className }: TaskGridProps) {
  return (
    <section className={cn("w-full px-4", className)}>
      <div className="max-w-6xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-8">
          <h2 className="font-display text-display-lg text-sara-text-primary mb-2">
            Clinical Workflows
          </h2>
          <p className="text-body text-sara-text-secondary">
            Select a task to start a conversation with Sara
          </p>
        </div>

        {/* Grid - 5 columns on large screens, 2 on medium, 1 on small */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {TASKS.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </div>
      </div>
    </section>
  );
}

export default TaskGrid;
