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
        // COBOL BMS color mappings to CSS
        "bms-blue": "#3b82f6",
        "bms-yellow": "#eab308",
        "bms-green": "#22c55e",
        "bms-turquoise": "#14b8a6",
        "bms-red": "#ef4444",
        "bms-neutral": "#9ca3af",
      },
      fontFamily: {
        mono: ["IBM Plex Mono", "Courier New", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
