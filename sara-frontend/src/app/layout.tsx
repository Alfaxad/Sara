import type { Metadata } from "next";
import { DM_Sans, Playfair_Display } from "next/font/google";
import "./globals.css";

// Body/UI Font - DM Sans
const dmSans = DM_Sans({
  subsets: ["latin"],
  weight: ["100", "200", "300", "400", "500", "600", "700", "800", "900", "1000"],
  variable: "--font-dm-sans",
  display: "swap",
});

// Display Font - Playfair Display
const playfair = Playfair_Display({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800", "900"],
  variable: "--font-playfair",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Sara - Clinical Workflow Agent",
  description:
    "Sara is an intelligent clinical workflow agent that assists healthcare professionals with patient management, clinical tasks, and medical documentation.",
  keywords: [
    "clinical workflow",
    "healthcare AI",
    "patient management",
    "medical assistant",
    "FHIR",
    "EHR",
  ],
  authors: [{ name: "Sara Team" }],
  viewport: "width=device-width, initial-scale=1",
  themeColor: "#0B0F14",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${dmSans.variable} ${playfair.variable} font-body antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
