// vite.config.ts
import { sveltekit } from "file:///Users/Jorge/Documents/kidyland/node_modules/.pnpm/@sveltejs+kit@1.30.4_svelte@4.2.20_vite@5.4.21/node_modules/@sveltejs/kit/src/exports/vite/index.js";
import { defineConfig } from "file:///Users/Jorge/Documents/kidyland/node_modules/.pnpm/vite@5.4.21_@types+node@20.19.25/node_modules/vite/dist/node/index.js";
import path from "path";
import { fileURLToPath } from "url";
import { viteStaticCopy } from "file:///Users/Jorge/Documents/kidyland/node_modules/.pnpm/vite-plugin-static-copy@3.1.4_vite@5.4.21/node_modules/vite-plugin-static-copy/dist/index.js";
var __vite_injected_original_import_meta_url = "file:///Users/Jorge/Documents/kidyland/apps/web/vite.config.ts";
var __dirname = path.dirname(fileURLToPath(__vite_injected_original_import_meta_url));
var vite_config_default = defineConfig({
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
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCIvVXNlcnMvSm9yZ2UvRG9jdW1lbnRzL2tpZHlsYW5kL2FwcHMvd2ViXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ZpbGVuYW1lID0gXCIvVXNlcnMvSm9yZ2UvRG9jdW1lbnRzL2tpZHlsYW5kL2FwcHMvd2ViL3ZpdGUuY29uZmlnLnRzXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ltcG9ydF9tZXRhX3VybCA9IFwiZmlsZTovLy9Vc2Vycy9Kb3JnZS9Eb2N1bWVudHMva2lkeWxhbmQvYXBwcy93ZWIvdml0ZS5jb25maWcudHNcIjtpbXBvcnQgeyBzdmVsdGVraXQgfSBmcm9tIFwiQHN2ZWx0ZWpzL2tpdC92aXRlXCI7XG5pbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tIFwidml0ZVwiO1xuaW1wb3J0IHBhdGggZnJvbSBcInBhdGhcIjtcbmltcG9ydCB7IGZpbGVVUkxUb1BhdGggfSBmcm9tIFwidXJsXCI7XG5pbXBvcnQgeyB2aXRlU3RhdGljQ29weSB9IGZyb20gXCJ2aXRlLXBsdWdpbi1zdGF0aWMtY29weVwiO1xuXG5jb25zdCBfX2Rpcm5hbWUgPSBwYXRoLmRpcm5hbWUoZmlsZVVSTFRvUGF0aChpbXBvcnQubWV0YS51cmwpKTtcblxuZXhwb3J0IGRlZmF1bHQgZGVmaW5lQ29uZmlnKHtcbiAgcGx1Z2luczogW1xuICAgIHN2ZWx0ZWtpdCgpLFxuICAgIHZpdGVTdGF0aWNDb3B5KHtcbiAgICAgIHRhcmdldHM6IFtcbiAgICAgICAge1xuICAgICAgICAgIC8vIFVzZSBFU00gZm9ybWF0IGZvciBGRm1wZWcgY29yZSBmaWxlcyAoY29tcGF0aWJsZSB3aXRoIGR5bmFtaWMgaW1wb3J0cyBpbiBWaXRlKVxuICAgICAgICAgIC8vIEVTTSBpcyB0aGUgcmVjb21tZW5kZWQgZm9ybWF0IGZvciBWaXRlL1N2ZWx0ZUtpdCBwcm9qZWN0c1xuICAgICAgICAgIHNyYzogXCJub2RlX21vZHVsZXMvQGZmbXBlZy9jb3JlL2Rpc3QvZXNtLypcIixcbiAgICAgICAgICBkZXN0OiBcImZmbXBlZy1jb3JlXCIsXG4gICAgICAgIH0sXG4gICAgICBdLFxuICAgIH0pLFxuICBdLFxuICBzZXJ2ZXI6IHtcbiAgICBwb3J0OiBwYXJzZUludChwcm9jZXNzLmVudi5QT1JUIHx8IFwiNTE3OVwiLCAxMCksXG4gICAgaG9zdDogdHJ1ZSxcbiAgICBmczogeyBhbGxvdzogWycuLiddIH0sXG4gICAgaGVhZGVyczoge1xuICAgICAgLy8gUmVxdWlyZWQgZm9yIEZGbXBlZy53YXNtIFNoYXJlZEFycmF5QnVmZmVyIHN1cHBvcnQgKGVuYWJsZXMgdGhyZWFkcyBhbmQgU0lNRCBvcHRpbWl6YXRpb25zKVxuICAgICAgJ0Nyb3NzLU9yaWdpbi1PcGVuZXItUG9saWN5JzogJ3NhbWUtb3JpZ2luJyxcbiAgICAgICdDcm9zcy1PcmlnaW4tRW1iZWRkZXItUG9saWN5JzogJ3JlcXVpcmUtY29ycCcsXG4gICAgfSxcbiAgfSxcbiAgcmVzb2x2ZToge1xuICAgIGFsaWFzOiB7XG4gICAgICAnJGxpYic6IHBhdGgucmVzb2x2ZShfX2Rpcm5hbWUsICcuL3NyYy9saWInKSxcbiAgICAgICdAa2lkeWxhbmQvc2hhcmVkJzogcGF0aC5yZXNvbHZlKF9fZGlybmFtZSwgJy4uLy4uL3BhY2thZ2VzL3NoYXJlZC9zcmMnKSxcbiAgICAgICdAa2lkeWxhbmQvdWknOiBwYXRoLnJlc29sdmUoX19kaXJuYW1lLCAnLi4vLi4vcGFja2FnZXMvdWkvc3JjJyksXG4gICAgICAnQGtpZHlsYW5kL3V0aWxzJzogcGF0aC5yZXNvbHZlKF9fZGlybmFtZSwgJy4uLy4uL3BhY2thZ2VzL3V0aWxzL3NyYycpLFxuICAgIH0sXG4gIH0sXG4gIG9wdGltaXplRGVwczoge1xuICAgIC8vIEV4Y2x1ZGUgRkZtcGVnIHBhY2thZ2VzIHRvIHByZXZlbnQgYnVuZGxpbmcgaXNzdWVzIHdpdGggV0FTTVxuICAgIC8vIEZGbXBlZyBjb3JlIGZpbGVzIGFyZSBzZXJ2ZWQgZnJvbSBzdGF0aWMvIGRpcmVjdG9yeSAoY29waWVkIGJ5IHZpdGUtcGx1Z2luLXN0YXRpYy1jb3B5KVxuICAgIGV4Y2x1ZGU6IFsnQHN2ZWx0ZWpzL2tpdCcsICdAZmZtcGVnL2ZmbXBlZycsICdAZmZtcGVnL3V0aWwnXSxcbiAgfSxcbiAgc3NyOiB7XG4gICAgZXh0ZXJuYWw6IFtcbiAgICAgICdAa2lkeWxhbmQvc2hhcmVkJyxcbiAgICAgICdAa2lkeWxhbmQvdWknLFxuICAgICAgJ0BraWR5bGFuZC91dGlscycsXG4gICAgICAvLyBGRm1wZWcgcGFja2FnZXMgYXJlIGJyb3dzZXItb25seSAodXNlIFdBU00pIGFuZCBzaG91bGQgbm90IGJlIHByb2Nlc3NlZCBpbiBTU1JcbiAgICAgICdAZmZtcGVnL2ZmbXBlZycsXG4gICAgICAnQGZmbXBlZy91dGlsJyxcbiAgICBdLFxuICB9LFxufSk7XG4iXSwKICAibWFwcGluZ3MiOiAiO0FBQTBTLFNBQVMsaUJBQWlCO0FBQ3BVLFNBQVMsb0JBQW9CO0FBQzdCLE9BQU8sVUFBVTtBQUNqQixTQUFTLHFCQUFxQjtBQUM5QixTQUFTLHNCQUFzQjtBQUp5SixJQUFNLDJDQUEyQztBQU16TyxJQUFNLFlBQVksS0FBSyxRQUFRLGNBQWMsd0NBQWUsQ0FBQztBQUU3RCxJQUFPLHNCQUFRLGFBQWE7QUFBQSxFQUMxQixTQUFTO0FBQUEsSUFDUCxVQUFVO0FBQUEsSUFDVixlQUFlO0FBQUEsTUFDYixTQUFTO0FBQUEsUUFDUDtBQUFBO0FBQUE7QUFBQSxVQUdFLEtBQUs7QUFBQSxVQUNMLE1BQU07QUFBQSxRQUNSO0FBQUEsTUFDRjtBQUFBLElBQ0YsQ0FBQztBQUFBLEVBQ0g7QUFBQSxFQUNBLFFBQVE7QUFBQSxJQUNOLE1BQU0sU0FBUyxRQUFRLElBQUksUUFBUSxRQUFRLEVBQUU7QUFBQSxJQUM3QyxNQUFNO0FBQUEsSUFDTixJQUFJLEVBQUUsT0FBTyxDQUFDLElBQUksRUFBRTtBQUFBLElBQ3BCLFNBQVM7QUFBQTtBQUFBLE1BRVAsOEJBQThCO0FBQUEsTUFDOUIsZ0NBQWdDO0FBQUEsSUFDbEM7QUFBQSxFQUNGO0FBQUEsRUFDQSxTQUFTO0FBQUEsSUFDUCxPQUFPO0FBQUEsTUFDTCxRQUFRLEtBQUssUUFBUSxXQUFXLFdBQVc7QUFBQSxNQUMzQyxvQkFBb0IsS0FBSyxRQUFRLFdBQVcsMkJBQTJCO0FBQUEsTUFDdkUsZ0JBQWdCLEtBQUssUUFBUSxXQUFXLHVCQUF1QjtBQUFBLE1BQy9ELG1CQUFtQixLQUFLLFFBQVEsV0FBVywwQkFBMEI7QUFBQSxJQUN2RTtBQUFBLEVBQ0Y7QUFBQSxFQUNBLGNBQWM7QUFBQTtBQUFBO0FBQUEsSUFHWixTQUFTLENBQUMsaUJBQWlCLGtCQUFrQixjQUFjO0FBQUEsRUFDN0Q7QUFBQSxFQUNBLEtBQUs7QUFBQSxJQUNILFVBQVU7QUFBQSxNQUNSO0FBQUEsTUFDQTtBQUFBLE1BQ0E7QUFBQTtBQUFBLE1BRUE7QUFBQSxNQUNBO0FBQUEsSUFDRjtBQUFBLEVBQ0Y7QUFDRixDQUFDOyIsCiAgIm5hbWVzIjogW10KfQo=
