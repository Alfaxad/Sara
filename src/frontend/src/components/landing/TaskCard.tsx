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
  index: number;
  className?: string;
}

export function TaskCard({ task, index, className }: TaskCardProps) {
  const IconComponent = iconMap[task.icon] || Activity;

  return (
    <Link href={`/chat/${task.id}`} className="block group">
      <div
        className={cn(
          "sara-card",
          "flex items-start gap-3.5",
          "cursor-pointer",
          "animate-card-in",
          className
        )}
        style={{ animationDelay: `${index * 45}ms` }}
      >
        {/* Icon */}
        <div className="sara-icon-box">
          <IconComponent className="w-[17px] h-[17px]" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h3 className="text-subheading text-sara-text-primary mb-1 group-hover:text-sara-accent transition-colors">
            {task.name}
          </h3>
          <p className="text-body-small text-sara-text-muted leading-snug">
            {task.description}
          </p>
        </div>
      </div>
    </Link>
  );
}

export default TaskCard;
