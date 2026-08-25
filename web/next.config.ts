import type { NextConfig } from "next";

// 静的 export のみ(N-03: v0.4 までサーバー実行を持たない)
const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
};

export default nextConfig;
