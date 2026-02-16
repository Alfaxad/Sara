export interface Task {
  id: string;
  name: string;
  description: string;
  icon: string;
  context: string;
  question: string;
}

export const TASKS: Task[] = [
  {
    id: "task1",
    name: "Patient Lookup",
    description: "Find patient by name and demographics",
    icon: "magnifying-glass",
    context: "Patient with name John Smith and DOB 1985-03-15",
    question: "What's the MRN?",
  },
  {
    id: "task2",
    name: "Medication Refill",
    description: "Refill an existing prescription",
    icon: "pill",
    context: "Patient S6200102",
    question: "Refill the current Metformin prescription",
  },
  {
    id: "task3",
    name: "Lab Order",
    description: "Order laboratory tests",
    icon: "flask-conical",
    context: "Patient S1032702",
    question: "Order a lipid panel",
  },
  {
    id: "task4",
    name: "Allergy Check",
    description: "Check documented allergies",
    icon: "clipboard-list",
    context: "Patient S2874590",
    question: "Check for penicillin allergies",
  },
  {
    id: "task5",
    name: "Dosing Calculation",
    description: "Calculate medication dosing",
    icon: "syringe",
    context: "Patient S9203482",
    question: "Calculate Metformin dose based on renal function",
  },
  {
    id: "task6",
    name: "Disease Summary",
    description: "Get condition management summary",
    icon: "bar-chart-3",
    context: "Patient S6200102",
    question: "Provide a diabetes management summary",
  },
  {
    id: "task7",
    name: "Vitals Recording",
    description: "Record patient vital signs",
    icon: "stethoscope",
    context: "Patient S7194920",
    question: "Record blood pressure 128/82 mmHg",
  },
  {
    id: "task8",
    name: "Lab Interpretation",
    description: "Interpret laboratory results",
    icon: "file-text",
    context: "Patient S4820395",
    question: "Interpret the most recent metabolic panel",
  },
  {
    id: "task9",
    name: "Condition Lookup",
    description: "View active medical conditions",
    icon: "activity",
    context: "Patient S3029402",
    question: "What active conditions are documented?",
  },
  {
    id: "task10",
    name: "Procedure History",
    description: "View past procedures",
    icon: "microscope",
    context: "Patient S8827743",
    question: "List procedures from the past 2 years",
  },
];
