import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || "",
  typescript: { ignoreBuildErrors: true },
  transpilePackages: ["agora-agent-client-toolkit", "@agora/agent-ui-kit"],
};

export default nextConfig;
