import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // BMS color mapping from spec section 1
        'bms-blue': '#3B82F6',      // BMS BLUE → text-blue-500
        'bms-green': '#22C55E',     // BMS GREEN → text-green-500
        'bms-red': '#EF4444',       // BMS RED → text-red-500
        'bms-yellow': '#EAB308',    // BMS YELLOW → text-yellow-500
        'bms-cyan': '#06B6D4',      // BMS TURQUOISE → text-cyan-500
        'bms-pink': '#EC4899',      // BMS PINK/MAGENTA (COPAU01 identity fields)
      },
    },
  },
  plugins: [],
};

export default config;
