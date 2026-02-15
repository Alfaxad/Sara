import { Hero, TaskGrid, Disclaimer } from "@/components/landing";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col">
      {/* Hero Section */}
      <Hero />

      {/* Task Grid */}
      <TaskGrid className="flex-1" />

      {/* Disclaimer */}
      <Disclaimer />
    </main>
  );
}
