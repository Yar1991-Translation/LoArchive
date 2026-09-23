import { fileURLToPath, URL } from "node:url";

import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vitest/config";

export default defineConfig({
  root: fileURLToPath(new URL("./frontend", import.meta.url)),
  plugins: [vue()],
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version ?? "0.0.0"),
  },
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./frontend/src", import.meta.url)),
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    // 开发时把 API 转发到本地 FastAPI 后端（npm run dev 会自动拉起后端）
    proxy: {
      "/api": {
        target: "http://127.0.0.1:5000",
        changeOrigin: true,
        configure: (proxy) => {
          // 后端启动需要数秒（或未单独启动时），静默等待而不是刷屏报错
          proxy.on("error", () => {});
        },
      },
    },
  },
  test: {
    // 测试文件放在仓库根的 tests-frontend/
    root: fileURLToPath(new URL(".", import.meta.url)),
    include: ["tests-frontend/**/*.test.ts"],
    setupFiles: ["tests-frontend/setup.ts"],
    environment: "jsdom",
    globals: true,
  },
});
