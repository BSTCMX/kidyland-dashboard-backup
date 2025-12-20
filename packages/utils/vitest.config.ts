import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
  },
  resolve: {
    alias: {
      "$app/environment": path.resolve(__dirname, "./tests/mocks/app-environment.ts"),
      "$app/navigation": path.resolve(__dirname, "./tests/mocks/app-navigation.ts"),
      "@kidyland/shared": path.resolve(__dirname, "../shared/src"),
    },
  },
});

