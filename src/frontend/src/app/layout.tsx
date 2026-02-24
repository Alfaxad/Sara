import type { Metadata, Viewport } from "next";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#000000",
};

export const metadata: Metadata = {
  title: {
    default: "Sara - Clinical Workflow Agent",
    template: "%s | Sara",
  },
  description:
    "Sara is an intelligent clinical workflow agent that assists healthcare professionals with patient management, clinical tasks, and medical documentation. Powered by AI and FHIR standards.",
  keywords: [
    "clinical workflow",
    "healthcare AI",
    "patient management",
    "medical assistant",
    "FHIR",
    "EHR",
    "clinical decision support",
    "medical AI",
    "healthcare automation",
  ],
  authors: [{ name: "Sara Team" }],
  creator: "Sara Team",
  publisher: "Sara",
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    title: "Sara - Clinical Workflow Agent",
    description:
      "A clinical workflow agent for physicians",
    type: "website",
    locale: "en_US",
    siteName: "Sara",
  },
  twitter: {
    card: "summary_large_image",
    title: "Sara - Clinical Workflow Agent",
    description:
      "A clinical workflow agent for physicians",
  },
  icons: {
    icon: [
      { url: "/icon.svg", type: "image/svg+xml" },
    ],
    apple: "/icon.svg",
  },
  manifest: "/manifest.json",
  category: "healthcare",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">
        {/* Skip link for keyboard navigation */}
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>
        <div id="main-content">{children}</div>
        <Analytics />
      </body>
    </html>
  );
}
