/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  images: {
    // Disable optimizer so any relative /media/... works without domain config
    unoptimized: true,
  },
  env: {
    NEXT_PUBLIC_API_BASE: process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api',
    NEXT_SERVER_API_BASE: process.env.NEXT_SERVER_API_BASE || 'http://backend:8000/api',
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://backend:8000/api/:path*',
      },
      {
        source: '/media/:path*',
        destination: 'http://backend:8000/media/:path*',
      },
    ];
  },
};

export default nextConfig;


