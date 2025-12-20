<script lang="ts">
  /**
   * ThemeToggle Component - Elegant theme switcher (inspired by JorgeLeal).
   * 
   * Toggles between light and dark mode with smooth animations.
   * Applies theme immediately without flash.
   */
  import { onMount } from "svelte";
  
  let currentTheme: "light" | "dark" = "light";
  let mounted = false;
  
  onMount(() => {
    // Get current theme from localStorage or system preference
    const storedTheme = localStorage.getItem("theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    currentTheme = (storedTheme as "light" | "dark") || (prefersDark ? "dark" : "light");
    mounted = true;
  });
  
  function toggleTheme() {
    const newTheme = currentTheme === "light" ? "dark" : "light";
    currentTheme = newTheme;
    
    // Apply theme
    if (newTheme === "dark") {
      document.documentElement.classList.add("dark");
      document.documentElement.setAttribute("data-theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      document.documentElement.setAttribute("data-theme", "light");
    }
    
    // Save to localStorage
    localStorage.setItem("theme", newTheme);
  }
</script>

<button
  class="theme-toggle"
  on:click={toggleTheme}
  aria-label="Toggle theme"
  title={currentTheme === "light" ? "Cambiar a modo oscuro" : "Cambiar a modo claro"}
>
  <div class="toggle-track" class:dark={currentTheme === "dark"}>
    <div class="toggle-thumb" class:dark={currentTheme === "dark"}>
      {#if mounted}
        {#if currentTheme === "light"}
          <!-- Sun icon -->
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="5"/>
            <line x1="12" y1="1" x2="12" y2="3"/>
            <line x1="12" y1="21" x2="12" y2="23"/>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
            <line x1="1" y1="12" x2="3" y2="12"/>
            <line x1="21" y1="12" x2="23" y2="12"/>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
          </svg>
        {:else}
          <!-- Moon icon -->
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
          </svg>
        {/if}
      {/if}
    </div>
  </div>
</button>

<style>
  .theme-toggle {
    position: relative;
    background: transparent;
    border: none;
    cursor: pointer;
    padding: 4px;
    border-radius: 24px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .theme-toggle:hover {
    transform: scale(1.05);
  }
  
  .theme-toggle:focus {
    outline: 2px solid var(--accent-primary);
    outline-offset: 2px;
  }
  
  .toggle-track {
    width: 56px;
    height: 28px;
    background: linear-gradient(to right, #0093f7, #3dad09);
    border-radius: 24px;
    padding: 2px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 
      inset 0 2px 4px rgba(0, 0, 0, 0.1),
      0 2px 8px rgba(0, 147, 247, 0.3);
  }
  
  .toggle-track.dark {
    background: linear-gradient(to right, #1a2035, #0f1629);
    box-shadow: 
      inset 0 2px 4px rgba(0, 0, 0, 0.3),
      0 2px 8px rgba(0, 0, 0, 0.5);
  }
  
  .toggle-thumb {
    width: 24px;
    height: 24px;
    background: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #0093f7;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    transform: translateX(0);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }
  
  .toggle-thumb.dark {
    transform: translateX(28px);
    background: #1a2035;
    color: #f8fafc;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
  }
  
  /* Responsive */
  @media (max-width: 768px) {
    .toggle-track {
      width: 48px;
      height: 24px;
    }
    
    .toggle-thumb {
      width: 20px;
      height: 20px;
    }
    
    .toggle-thumb.dark {
      transform: translateX(24px);
    }
    
    .toggle-thumb svg {
      width: 12px;
      height: 12px;
    }
  }
</style>
