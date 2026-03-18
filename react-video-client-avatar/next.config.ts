import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || "",
  typescript: { ignoreBuildErrors: true },
  transpilePackages: ["agora-agent-client-toolkit", "@agora/agent-ui-kit"],
  headers: async () => [
    {
      source: "/(.*)",
      headers: [
        { key: "Cross-Origin-Embedder-Policy", value: "credentialless" },
        { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
      ],
    },
  ],
};

export default nextConfig;
