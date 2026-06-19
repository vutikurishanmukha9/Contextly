import { defineConfig, mergeConfig } from "vitest/config";
import viteConfig from "./vite.config";
import { resolve } from "path";

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      globals: true,
      environment: "jsdom",
      setupFiles: ["./src/__tests__/setup.ts"],
      include: ["src/**/*.{test,spec}.{ts,tsx}"],
      css: false,
    },
    resolve: {
      alias: {
        "@": resolve(__dirname, "./src")
      }
    }
  }),
);
