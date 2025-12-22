/**
 * Vite environment types.
 * 
 * Clean Architecture: Type definitions for Vite-specific globals.
 * These types are injected by Vite at build time, but we need to declare
 * them for TypeScript type checking in the shared package.
 * 
 * This file ensures that `import.meta.env` is properly typed when
 * typechecking packages/utils in isolation.
 */

/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  readonly MODE: string;
  readonly DEV: boolean;
  readonly PROD: boolean;
  readonly SSR: boolean;
  // Add other env variables as needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

