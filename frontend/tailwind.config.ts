import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      // BMS color attribute mapping (from 03-frontend-specification.md section 1)
      colors: {
        bms: {
          blue: '#3b82f6',       // BLUE — labels, read-only fields (ASKIP BLUE)
          yellow: '#eab308',     // YELLOW — title lines (TITLE01O, TITLE02O)
          turquoise: '#06b6d4',  // TURQUOISE — field labels/prompts (e.g. "User ID :")
          green: '#22c55e',      // GREEN — input field values (UNPROT GREEN)
          red: '#ef4444',        // RED — error messages (DFHRED, ERRMSG BRT)
          neutral: '#6b7280',    // NEUTRAL — default text
          pink: '#ec4899',       // PINK — authorization detail fields
          success: '#16a34a',    // DFHGREEN — success messages
        },
      },
      fontFamily: {
        // Monospace for list screens that require column alignment
        // Matches 3270 terminal character-aligned display
        mono: ['Courier New', 'Courier', 'monospace'],
      },
    },
  },
  plugins: [],
};

export default config;
