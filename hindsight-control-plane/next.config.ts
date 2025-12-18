import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  output: 'standalone',
  // Disable request logging in production
  logging: false,
  // Set the monorepo root explicitly to avoid detecting wrong lockfiles in parent directories
  turbopack: {
    root: path.resolve(__dirname, '..'),
  },
};

export default nextConfig;
