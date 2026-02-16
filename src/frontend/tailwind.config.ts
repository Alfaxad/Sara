import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // Sara Monochromatic Color System
      colors: {
        sara: {
          // Backgrounds
          "bg-base": "var(--sara-bg-base)",
          "bg-surface": "var(--sara-bg-surface)",
          "bg-elevated": "var(--sara-bg-elevated)",
          "bg-subtle": "var(--sara-bg-subtle)",

          // Text
          "text-primary": "var(--sara-text-primary)",
          "text-secondary": "var(--sara-text-secondary)",
          "text-muted": "var(--sara-text-muted)",
          "text-dim": "var(--sara-text-dim)",

          // Borders
          border: "var(--sara-border)",
          "border-hover": "var(--sara-border-hover)",
          "border-focus": "var(--sara-border-focus)",

          // Accent (white-based)
          accent: "var(--sara-accent)",
          "accent-hover": "var(--sara-accent-hover)",
          "accent-soft": "var(--sara-accent-soft)",
          "accent-muted": "var(--sara-accent-muted)",

          // Semantic
          success: "var(--sara-success)",
          "success-soft": "var(--sara-success-soft)",
          warning: "var(--sara-warning)",
          "warning-soft": "var(--sara-warning-soft)",
          error: "var(--sara-error)",
          "error-soft": "var(--sara-error-soft)",
          info: "var(--sara-info)",
          "info-soft": "var(--sara-info-soft)",
        },
      },

      // System font stack
      fontFamily: {
        sans: [
          "-apple-system",
          "SF Pro Display",
          "Helvetica Neue",
          "system-ui",
          "sans-serif",
        ],
      },

      // Type Scale
      fontSize: {
        "display-xl": [
          "40px",
          { lineHeight: "1.1", fontWeight: "500", letterSpacing: "-0.04em" },
        ],
        "display-lg": [
          "28px",
          { lineHeight: "1.2", fontWeight: "500", letterSpacing: "-0.03em" },
        ],
        heading: [
          "15px",
          { lineHeight: "1.4", fontWeight: "500", letterSpacing: "-0.02em" },
        ],
        subheading: [
          "14px",
          { lineHeight: "1.5", fontWeight: "500", letterSpacing: "-0.01em" },
        ],
        body: ["14px", { lineHeight: "1.6", fontWeight: "400" }],
        "body-small": [
          "13px",
          { lineHeight: "1.55", fontWeight: "400" },
        ],
        caption: [
          "11px",
          { lineHeight: "1.4", fontWeight: "500", letterSpacing: "0.02em" },
        ],
      },

      // Spacing
      spacing: {
        "18": "4.5rem",
        "88": "22rem",
        "128": "32rem",
      },

      // Border Radius
      borderRadius: {
        sara: "12px",
        "sara-sm": "10px",
        "sara-lg": "14px",
        "sara-full": "28px",
      },

      // Animations
      animation: {
        "card-in": "cardIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) both",
        "msg-in": "msgIn 0.35s cubic-bezier(0.16, 1, 0.3, 1) both",
        "fade-up": "fadeUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) both",
        "status-pulse": "statusPulse 2s infinite",
        "sara-spin": "sara-spin 1s linear infinite",
      },

      keyframes: {
        cardIn: {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        msgIn: {
          from: { opacity: "0", transform: "translateY(5px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        fadeUp: {
          from: { opacity: "0", transform: "translateY(10px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        statusPulse: {
          "0%, 100%": { opacity: "0.6" },
          "50%": { opacity: "1" },
        },
        "sara-spin": {
          from: { transform: "rotate(0deg)" },
          to: { transform: "rotate(360deg)" },
        },
      },

      // Transition
      transitionDuration: {
        sara: "150ms",
      },

      transitionTimingFunction: {
        sara: "cubic-bezier(0.16, 1, 0.3, 1)",
      },
    },
  },
  plugins: [],
};

export default config;
