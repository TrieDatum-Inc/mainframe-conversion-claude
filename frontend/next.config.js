/** @type {import('next').NextConfig} */
const nextConfig = {
  // API base URL — points to FastAPI backend
  // In development: http://localhost:8000
  // In production: set via NEXT_PUBLIC_API_URL environment variable
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },

  // Strict mode for development — helps catch issues early
  reactStrictMode: true,

  // Content Security Policy headers
  // Prevents XSS attacks — replaces COBOL's implicit terminal-side input filtering
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
