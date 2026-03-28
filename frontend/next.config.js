/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow long-running API routes (local LLM can be slow)
  experimental: {
    // serverActions timeout (Next.js 14+)
  },
  // Proxy rewrites so the frontend can call /api/* without CORS in production
  async rewrites() {
    return [
      {
        source: "/proxy/:path*",
        destination: "http://localhost:8000/:path*",
      },
    ];
  },
};

module.exports = nextConfig;