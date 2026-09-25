import type { NextConfig } from "next";
const config: NextConfig = {
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || "",
  skipTrailingSlashRedirect: Boolean(process.env.NEXT_PUBLIC_BASE_PATH),
  experimental: { proxyTimeout: 600_000, proxyClientMaxBodySize: "34mb" },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: (process.env.SCI_BACKEND_URL || "http://127.0.0.1:8010") + "/api/:path*",
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
        ],
      },
    ];
  },
};
export default config;
