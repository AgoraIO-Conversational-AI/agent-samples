import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  transpilePackages: [
    "@agora/conversational-ai",
    "@agora/conversational-ai-react",
    "@agora/agent-ui-kit",
  ],
}

export default nextConfig
