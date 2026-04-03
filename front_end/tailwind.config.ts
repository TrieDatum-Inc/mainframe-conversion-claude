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
        // CardDemo brand palette mirroring BMS color attributes
        "bms-blue": "#1e40af",
        "bms-yellow": "#ca8a04",
        "bms-turquoise": "#0891b2",
        "bms-green": "#15803d",
        "bms-red": "#dc2626",
        "bms-neutral": "#6b7280",
      },
    },
  },
  plugins: [],
};
export default config;
