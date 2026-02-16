"use client";

import Link from "next/link";
import {
  Search,
  Pill,
  FlaskConical,
  ClipboardList,
  Syringe,
  BarChart3,
  Stethoscope,
  FileText,
  Activity,
  Microscope,
  LucideIcon,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/utils";
import type { Task } from "@/lib/tasks";

const iconMap: Record<string, LucideIcon> = {
  "magnifying-glass": Search,
  pill: Pill,
  "flask-conical": FlaskConical,
  "clipboard-list": ClipboardList,
  syringe: Syringe,
  "bar-chart-3": BarChart3,
  stethoscope: Stethoscope,
  "file-text": FileText,
  activity: Activity,
  microscope: Microscope,
};

export interface TaskCardProps {
  task: Task;
  className?: string;
}

export function TaskCard({ task, className }: TaskCardProps) {
  const IconComponent = iconMap[task.icon] || Activity;

  return (
    <Link href={`/chat/${task.id}`} className="block group">
      <Card
        variant="surface"
        className={cn(
          "h-full cursor-pointer",
          "border border-sara-border",
          "hover:bg-sara-bg-elevated hover:border-sara-accent-soft",
          "hover:shadow-sara-glow",
          "transition-all duration-200",
          "group-focus-visible:ring-2 group-focus-visible:ring-sara-border-focus",
          className
        )}
      >
        <div className="flex items-start gap-4">
          {/* Icon */}
          <div className="flex-shrink-0 w-10 h-10 rounded-sara-sm bg-sara-accent-soft flex items-center justify-center">
            <IconComponent className="w-5 h-5 text-sara-accent" />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <h3 className="font-body text-subheading text-sara-text-primary mb-1 group-hover:text-sara-accent transition-colors">
              {task.name}
            </h3>
            <p className="text-body-small text-sara-text-secondary line-clamp-2">
              {task.description}
            </p>
          </div>
        </div>
      </Card>
    </Link>
  );
}

export default TaskCard;
