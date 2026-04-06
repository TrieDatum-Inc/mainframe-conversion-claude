/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Allow backend API calls from the frontend container
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
