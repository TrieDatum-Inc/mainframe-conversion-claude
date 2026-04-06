import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // CardDemo mainframe-inspired palette
        mainframe: {
          bg: "#0a0a0a",
          text: "#00ff41",
          dim: "#007a1e",
          header: "#1a1a2e",
          panel: "#16213e",
          border: "#0f3460",
          highlight: "#e94560",
          info: "#53d8fb",
          warn: "#f5a623",
          error: "#ff4757",
          success: "#2ed573",
        },
      },
      fontFamily: {
        mono: ["Courier New", "Courier", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
