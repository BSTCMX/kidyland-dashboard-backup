/**
 * Theme store for dark/light mode management.
 * 
 * Supports 'light', 'dark', and 'system' (follows OS preference) themes.
 */
import { writable, derived, get } from "svelte/store";
import { browser } from "$app/environment";

export type Theme = "light" | "dark" | "system";

const THEME_STORAGE_KEY = "kidyland_theme";

// Get initial theme from localStorage or system preference
function getInitialTheme(): Theme {
  if (!browser) return "system";
  
  const stored = localStorage.getItem(THEME_STORAGE_KEY) as Theme | null;
  if (stored && ["light", "dark", "system"].includes(stored)) {
    return stored;
  }
  
  return "system";
}

export const themeStore = writable<Theme>(getInitialTheme());

// Derived store for actual theme (resolves 'system' to 'light' or 'dark')
export const resolvedTheme = derived(themeStore, ($theme) => {
  if ($theme === "system" && browser) {
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }
  return $theme === "system" ? "light" : $theme;
});

// Apply theme to document
if (browser) {
  resolvedTheme.subscribe((theme) => {
    document.documentElement.setAttribute("data-theme", theme);
    document.documentElement.classList.toggle("dark", theme === "dark");
  });
  
  // Watch for system theme changes
  window
    .matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", () => {
      const currentTheme = get(themeStore);
      if (currentTheme === "system") {
        // Trigger update by setting the same value
        themeStore.set("system");
      }
    });
}

// Sync to localStorage
themeStore.subscribe((theme) => {
  if (browser) {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }
});

/**
 * Set theme programmatically.
 */
export function setTheme(theme: Theme): void {
  themeStore.set(theme);
}

/**
 * Toggle between light and dark (skips 'system').
 */
export function toggleTheme(): void {
  const current = get(themeStore);
  if (current === "light") {
    setTheme("dark");
  } else if (current === "dark") {
    setTheme("light");
  } else {
    // If system, switch to opposite of current resolved theme
    const resolved = get(resolvedTheme);
    setTheme(resolved === "dark" ? "light" : "dark");
  }
}


