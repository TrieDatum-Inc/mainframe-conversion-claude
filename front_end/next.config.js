/** @type {import('next').NextConfig} */
const nextConfig = {
  // Content Security Policy — replaces BMS implicit terminal-only access
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-eval' 'unsafe-inline'", // unsafe-* for Next.js dev mode
              "style-src 'self' 'unsafe-inline'",
              "img-src 'self' data:",
              "font-src 'self'",
              "connect-src 'self' http://localhost:8000 https://localhost:8000",
            ].join("; "),
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
