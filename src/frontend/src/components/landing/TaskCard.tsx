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
  const isFeatured = task.id === "iris-summary";

  return (
    <Link href={`/chat/${task.id}`} className="block group">
      <div
        className={cn(
          "sara-card",
          "flex min-h-[90px] items-center gap-4",
          "cursor-pointer",
          "animate-card-in",
          isFeatured && "sara-card-featured",
          className
        )}
        style={{ animationDelay: `${index * 45}ms` }}
      >
        <div className={cn("sara-icon-box", isFeatured && "sara-icon-box-featured")}>
          <IconComponent className="w-[17px] h-[17px]" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="mb-1 flex items-center gap-2">
            <h3 className="text-subheading text-sara-text-primary group-hover:text-sara-accent transition-colors">
              {task.name}
            </h3>
            {isFeatured && <span className="sara-card-kicker">IRIS</span>}
          </div>
          <p className="text-body-small text-sara-text-muted leading-snug">
            {task.description}
          </p>
        </div>
      </div>
    </Link>
  );
}

export default TaskCard;
