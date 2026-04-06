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
        // BMS color palette equivalents
        // COLOR=GREEN  → COBOL screen labels, prompts
        // COLOR=YELLOW → Screen titles
        // COLOR=BLUE   → Menu options, field labels
        // COLOR=RED    → Error messages (DFHRED)
        // COLOR=TURQUOISE → Section headers
      },
    },
  },
  plugins: [],
};

export default config;
