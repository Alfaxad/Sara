import type { Metadata, Viewport } from "next";
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

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0B0F14",
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
      "AI-powered clinical workflow assistant for healthcare professionals",
    type: "website",
    locale: "en_US",
    siteName: "Sara",
  },
  twitter: {
    card: "summary_large_image",
    title: "Sara - Clinical Workflow Agent",
    description:
      "AI-powered clinical workflow assistant for healthcare professionals",
  },
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/icon.svg", type: "image/svg+xml" },
    ],
    apple: "/apple-touch-icon.png",
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
      <body
        className={`${dmSans.variable} ${playfair.variable} font-body antialiased`}
      >
        {/* Skip link for keyboard navigation */}
        <a
          href="#main-content"
          className="skip-link"
        >
          Skip to main content
        </a>
        <div id="main-content">
          {children}
        </div>
      </body>
    </html>
  );
}
