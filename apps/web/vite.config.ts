// vite.config.ts
import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";
import path from "path";
import { fileURLToPath } from "url";
import { viteStaticCopy } from "vite-plugin-static-copy";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [
    sveltekit(),
    viteStaticCopy({
      targets: [
        {
          // Use ESM format for FFmpeg core files (compatible with dynamic imports in Vite)
          // ESM is the recommended format for Vite/SvelteKit projects
          src: "node_modules/@ffmpeg/core/dist/esm/*",
          dest: "ffmpeg-core"
        }
      ]
    })
  ],
  server: {
    port: parseInt(process.env.PORT || "5179", 10),
    host: true,
    fs: { allow: [".."] },
    headers: {
      // Required for FFmpeg.wasm SharedArrayBuffer support (enables threads and SIMD optimizations)
      "Cross-Origin-Opener-Policy": "same-origin",
      "Cross-Origin-Embedder-Policy": "require-corp"
    }
  },
  resolve: {
    alias: {
      "$lib": path.resolve(__dirname, "./src/lib"),
      "@kidyland/shared": path.resolve(__dirname, "../../packages/shared/src"),
      "@kidyland/ui": path.resolve(__dirname, "../../packages/ui/src"),
      "@kidyland/utils": path.resolve(__dirname, "../../packages/utils/src")
    }
  },
  optimizeDeps: {
    // Exclude FFmpeg packages to prevent bundling issues with WASM
    // FFmpeg core files are served from static/ directory (copied by vite-plugin-static-copy)
    exclude: ["@sveltejs/kit", "@ffmpeg/ffmpeg", "@ffmpeg/util"]
  },
  ssr: {
    external: [
      "@kidyland/shared",
      "@kidyland/ui",
      "@kidyland/utils",
      // FFmpeg packages are browser-only (use WASM) and should not be processed in SSR
      "@ffmpeg/ffmpeg",
      "@ffmpeg/util"
    ]
  }
});
