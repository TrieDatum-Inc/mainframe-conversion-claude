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
        // CardDemo BMS color palette mapped to Tailwind
        'bms-blue': '#2563eb',
        'bms-yellow': '#ca8a04',
        'bms-green': '#16a34a',
        'bms-red': '#dc2626',
        'bms-turquoise': '#0891b2',
        'bms-neutral': '#6b7280',
      },
    },
  },
  plugins: [],
};

export default config;
