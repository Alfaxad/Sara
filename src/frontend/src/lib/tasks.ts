export interface Task {
  id: string;
  name: string;
  description: string;
  icon: string;
  context: string;
  question: string;
}

// These tasks match the exact examples from MedAgentBench test_data_v2.json
// The backend serves these via /api/tasks
export const TASKS: Task[] = [
  {
    id: "task1",
    name: "Patient Lookup",
    description: "Find patient by name and DOB to get their MRN",
    icon: "magnifying-glass",
    context: "",
    question: "What's the MRN of the patient with name Peter Stafford and DOB of 1932-12-29? If the patient does not exist, the answer should be \"Patient not found\"",
  },
  {
    id: "task2",
    name: "Patient Age",
    description: "Calculate patient age from their medical record",
    icon: "activity",
    context: "It's 2023-11-13T10:15:00+00:00 now, and the answer should be rounded down to an integer.",
    question: "What's the age of the patient with MRN of S2874099?",
  },
  {
    id: "task3",
    name: "Record Vitals",
    description: "Record blood pressure measurement for a patient",
    icon: "stethoscope",
    context: "It's 2023-11-13T10:15:00+00:00 now. The flowsheet ID for blood pressure is BP.",
    question: "I just measured the blood pressure for patient with MRN of S2380121, and it is \"118/77 mmHg\". Help me record it.",
  },
  {
    id: "task4",
    name: "Lab Results",
    description: "Check recent magnesium level for a patient",
    icon: "flask-conical",
    context: "It's 2023-11-13T10:15:00+00:00 now. The code for magnesium is \"MG\". The answer should be a single number converted to a unit of mg/dL, and it should be -1 if a measurement within last 24 hours is not available.",
    question: "What's the most recent magnesium level of the patient S3032536 within last 24 hours?",
  },
  {
    id: "task5",
    name: "Check & Order",
    description: "Check magnesium and order replacement if low",
    icon: "syringe",
    context: "It's 2023-11-13T10:15:00+00:00 now. The code for magnesium is \"MG\". The NDC for replacement IV magnesium is 0338-1715-40. Dosing instructions: (1) Mild deficiency (eg, serum magnesium 1.5 to 1.9 mg/dL): IV: 1 g over 1 hour. (2) Moderate deficiency (eg, serum magnesium 1 to <1.5 mg/dL): IV: 2 g over 2 hours. (3) Severe deficiency (eg, serum magnesium <1 mg/dL): IV: 4 g over 4 hours.",
    question: "Check patient S3084624's last serum magnesium level within last 24 hours. If low, then order replacement IV magnesium according to dosing instructions. If no magnesium level has been recorded in the last 24 hours, don't order anything.",
  },
  {
    id: "task6",
    name: "Average CBG",
    description: "Calculate average blood glucose over 24 hours",
    icon: "bar-chart-3",
    context: "It's 2023-11-13T10:15:00+00:00 now. The code for CBG is \"GLU\". The answer should be a single number converted to a unit of mg/dL, and it should be -1 if a measurement within last 24 hours is not available.",
    question: "What is the average CBG of the patient S6307599 over the last 24 hours?",
  },
  {
    id: "task7",
    name: "Recent CBG",
    description: "Get most recent blood glucose value",
    icon: "activity",
    context: "It's 2023-11-13T10:15:00+00:00 now. The code for CBG is \"GLU\"",
    question: "What is the most recent CBG of the patient S2197736?",
  },
  {
    id: "task8",
    name: "Order Referral",
    description: "Create orthopedic surgery referral with clinical notes",
    icon: "file-text",
    context: "It's 2023-11-13T10:15:00+00:00 now. The SNOMED code for orthopedic surgery referral is 306181000000106.",
    question: "Order orthopedic surgery referral for patient S2016972. Specify within the free text of the referral, \"Situation: acute left knee injury, Background: radiology report indicates ACL tear. Assessment: ACL tear grade II. Recommendation: request for Orthopedic service to evaluate and provide management recommendations.\"",
  },
  {
    id: "task9",
    name: "K+ Check & Order",
    description: "Check potassium and order replacement with follow-up lab",
    icon: "pill",
    context: "It's 2023-11-13T10:15:00+00:00 now. The code for potassium is \"K\". The NDC for replacement potassium is 40032-917-01. Dosing instructions: for every 0.1 mEq/L (or mmol/L) below threshold, order 10 mEq potassium oral repletion) to reach a goal of 3.5 serum level. The LOINC code for serum potassium level is 2823-3.",
    question: "Check patient S3241217's most recent potassium level. If low, then order replacement potassium according to dosing instructions. Also pair this order with a morning serum potassium level to be completed the next day at 8am.",
  },
  {
    id: "task10",
    name: "HbA1C Check",
    description: "Check HbA1C and order new test if needed",
    icon: "microscope",
    context: "It's 2023-11-13T10:15:00+00:00 now. The code for HbA1C is \"A1C\". The LOINC code for ordering HbA1C lab is: 4548-4. The answer should be [-1] if a measurement is not available.",
    question: "What's the last HbA1C (hemoglobin A1C) value in the chart for patient S1311412 and when was it recorded? If the lab value result date is greater than 1 year old, order a new HbA1C lab test.",
  },
];
