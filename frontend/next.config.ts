import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Every page in this app is a client component talking to the FastAPI
  // backend over fetch() — nothing depends on a Next.js server (no server
  // components fetching data, no route handlers), so a static export
  // deploys as a free static site instead of a paid always-on Node service.
  output: "export",
  // Emits /dashboard/goals/index.html instead of /dashboard/goals.html —
  // every static host serves a directory's index.html for a clean URL
  // automatically, without needing host-specific rewrite rules.
  trailingSlash: true,
};

export default nextConfig;
