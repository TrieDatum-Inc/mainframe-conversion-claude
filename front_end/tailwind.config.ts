import type { Config } from "tailwindcss";
const config: Config = {
  content: ["./src/pages/**/*.{js,ts,jsx,tsx,mdx}", "./src/components/**/*.{js,ts,jsx,tsx,mdx}", "./src/app/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: { extend: { colors: { "bms-blue": "#4444ff", "bms-yellow": "#ffff00", "bms-green": "#00cc00", "bms-turquoise": "#00cccc", "bms-red": "#ff4444" } } },
  plugins: [],
};
export default config;
