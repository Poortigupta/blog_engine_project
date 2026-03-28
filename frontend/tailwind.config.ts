import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["var(--font-display)"],
        body: ["var(--font-body)"],
        mono: ["var(--font-mono)", "monospace"],
      },
      colors: {
        ink: {
          DEFAULT: "#0a0a0f",
          soft: "#13131a",
          muted: "#1e1e2a",
        },
        acid: {
          DEFAULT: "#c8f135",
          dim: "#a0c128",
          glow: "#d4ff40",
        },
        frost: {
          DEFAULT: "#e8eaf0",
          muted: "#9499b0",
          dim: "#565b75",
        },
        signal: {
          red: "#ff4545",
          amber: "#ffb830",
          green: "#35f1a0",
        },
      },
      backgroundImage: {
        "grid-pattern": "linear-gradient(rgba(200,241,53,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(200,241,53,0.04) 1px, transparent 1px)",
        "noise": "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.05'/%3E%3C/svg%3E\")",
      },
    },
  },
  plugins: [],
};

export default config;