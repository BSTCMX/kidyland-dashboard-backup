// Template for SvelteKit apps
// Copy this to apps/<app-name>/.eslintrc.cjs
module.exports = {
  root: true,
  extends: ["../../.eslintrc.cjs"],
  parserOptions: {
    project: ["./tsconfig.json"],
    extraFileExtensions: [".svelte"],
  },
  env: {
    browser: true,
    node: true,
  },
  overrides: [
    {
      files: ["*.svelte"],
      parser: "svelte-eslint-parser",
      parserOptions: {
        parser: "@typescript-eslint/parser",
      },
    },
  ],
};
































