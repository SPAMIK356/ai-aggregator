/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  env: {
    NEXT_PUBLIC_API_BASE: process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000/api',
  },
  async rewrites() {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
    return [
      {
        source: '/api/:path*',
        destination: `${apiBase}/:path*`,
      },
    ];
  },
};

export default nextConfig;


