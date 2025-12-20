import { defineConfig } from 'vitest/config';
import { sveltekit } from '@sveltejs/kit/vite';
import path from 'path';

export default defineConfig({
  plugins: [sveltekit()],
  test: {
    include: ['src/**/*.{test,spec}.{js,ts,svelte}'],
    environment: 'jsdom',
    setupFiles: ['./src/tests/setup.ts'],
    globals: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/tests/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/types.ts',
        '**/+*.{js,ts,svelte}',
        '**/+page*.{js,ts,svelte}',
        '**/+layout*.{js,ts,svelte}',
        '**/+error*.{js,ts,svelte}',
      ],
      thresholds: {
        lines: 60,
        functions: 60,
        branches: 60,
        statements: 60,
      },
    },
  },
  resolve: {
    alias: {
      '$lib': path.resolve(__dirname, './src/lib'),
      '@kidyland/shared': path.resolve(__dirname, '../../packages/shared/src'),
      '@kidyland/ui': path.resolve(__dirname, '../../packages/ui/src'),
      '@kidyland/utils': path.resolve(__dirname, '../../packages/utils/src'),
    },
  },
});





























