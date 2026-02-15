import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // Sara Design System Colors
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

          // Borders
          border: "var(--sara-border)",
          "border-focus": "var(--sara-border-focus)",

          // Accent
          accent: "var(--sara-accent)",
          "accent-hover": "var(--sara-accent-hover)",
          "accent-soft": "var(--sara-accent-soft)",
          "accent-glow": "var(--sara-accent-glow)",
          secondary: "var(--sara-secondary)",
          "secondary-soft": "var(--sara-secondary-soft)",

          // Semantic
          critical: "var(--sara-critical)",
          "critical-soft": "var(--sara-critical-soft)",
          warning: "var(--sara-warning)",
          "warning-soft": "var(--sara-warning-soft)",
          success: "var(--sara-success)",
          "success-soft": "var(--sara-success-soft)",
          info: "var(--sara-info)",
          "info-soft": "var(--sara-info-soft)",
        },
      },

      // Sara Font Families
      fontFamily: {
        display: ["var(--font-playfair)", "Georgia", "serif"],
        body: ["var(--font-dm-sans)", "system-ui", "sans-serif"],
      },

      // Sara Type Scale
      fontSize: {
        "display-xl": [
          "2.25rem",
          { lineHeight: "1.2", fontWeight: "700", letterSpacing: "-0.02em" },
        ],
        "display-lg": [
          "1.75rem",
          { lineHeight: "1.3", fontWeight: "600", letterSpacing: "-0.01em" },
        ],
        heading: ["1.25rem", { lineHeight: "1.4", fontWeight: "600" }],
        subheading: ["1rem", { lineHeight: "1.5", fontWeight: "600" }],
        body: ["0.9375rem", { lineHeight: "1.6", fontWeight: "400" }],
        "body-small": ["0.8125rem", { lineHeight: "1.5", fontWeight: "400" }],
        caption: [
          "0.6875rem",
          { lineHeight: "1.4", fontWeight: "500", letterSpacing: "0.02em" },
        ],
      },

      // Custom Spacing
      spacing: {
        "18": "4.5rem",
        "88": "22rem",
        "128": "32rem",
      },

      // Border Radius
      borderRadius: {
        sara: "0.75rem",
        "sara-sm": "0.5rem",
        "sara-lg": "1rem",
      },

      // Box Shadow
      boxShadow: {
        sara: "0 4px 24px rgba(0, 0, 0, 0.25)",
        "sara-glow": "0 0 20px var(--sara-accent-glow)",
        "sara-elevated": "0 8px 32px rgba(0, 0, 0, 0.35)",
      },

      // Animations
      animation: {
        "sara-pulse": "sara-pulse 2s ease-in-out infinite",
        "sara-fade-in": "sara-fade-in 0.3s ease-out",
        "sara-slide-up": "sara-slide-up 0.3s ease-out",
        "sara-spin": "sara-spin 1s linear infinite",
      },

      keyframes: {
        "sara-pulse": {
          "0%, 100%": { boxShadow: "0 0 0 0 var(--sara-accent-glow)" },
          "50%": { boxShadow: "0 0 16px 4px var(--sara-accent-glow)" },
        },
        "sara-fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "sara-slide-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "sara-spin": {
          from: { transform: "rotate(0deg)" },
          to: { transform: "rotate(360deg)" },
        },
      },

      // Backdrop Blur
      backdropBlur: {
        sara: "12px",
      },

      // Transition
      transitionDuration: {
        sara: "200ms",
      },
    },
  },
  plugins: [],
};

export default config;
