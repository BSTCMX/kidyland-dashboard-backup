<script lang="ts">
  /**
   * AnimatedTitle Component - Reusable text title with layered shadow effect.
   * 
   * Clean Architecture: Reusable component in shared components.
   * 
   * Features:
   * - Layered text-shadow effect using project color palette
   * - Adapts to light/dark mode automatically
   * - Uses project color palette (CSS variables)
   * - Responsive and performant
   * 
   * Props:
   * - text: string - Text to display
   * - size: 'sm' | 'md' | 'lg' | 'xl' - Size variant
   */
  
  export let text: string = "Kidyland";
  export let size: "sm" | "md" | "lg" | "xl" = "lg";
</script>

<h1 class="animated-title title-{size}">
  {text}
</h1>

<style>
  @import url('https://fonts.googleapis.com/css2?family=Abril+Fatface&display=swap');
  
  .animated-title {
    font-family: 'Abril Fatface', var(--font-primary, system-ui, sans-serif);
    font-size: var(--title-font-size, 6rem);
    font-weight: 400;
    text-align: center;
    height: auto;
    line-height: 1.1;
    color: var(--text-primary, #fcedd8);
    margin: var(--spacing-md) auto var(--spacing-sm);
    position: relative;
    padding: var(--spacing-md) 0;
    overflow: visible;
    word-wrap: break-word;
    
    /* Smooth transitions for theme changes */
    transition: color 0.3s ease, text-shadow 0.3s ease;
  }
  
  /* Size variants - adapted for login page */
  .title-sm {
    --title-font-size: 2.5rem;
  }
  
  .title-md {
    --title-font-size: 3.5rem;
  }
  
  .title-lg {
    --title-font-size: 5rem;
  }
  
  .title-xl {
    --title-font-size: 7rem;
  }
  
  /* Dark mode adjustments - layered text-shadow with Kidyland colors */
  :global([data-theme="dark"]) .animated-title {
    color: var(--text-primary, #fcedd8);
    /* Layered text-shadow effect for dark mode - vibrant colors on dark background */
    text-shadow: 
      2px 2px 0px var(--kidyland-blue, #0093f7),
      4px 4px 0px var(--kidyland-green, #3dad09),
      6px 6px 0px var(--kidyland-pink, #d30554),
      8px 8px 0px var(--kidyland-yellow, #ffce00),
      10px 10px 0px var(--kidyland-blue, #0093f7),
      12px 12px 0px var(--kidyland-green, #3dad09),
      14px 14px 0px var(--kidyland-pink, #d30554),
      16px 16px 0px var(--kidyland-yellow, #ffce00),
      18px 18px 0px var(--kidyland-blue, #0093f7);
  }
  
  /* Light mode adjustments */
  :global(:root:not([data-theme="dark"])) .animated-title {
    color: var(--text-primary, #0f172a);
    /* Layered text-shadow effect for light mode - reduced offset for card containment */
    text-shadow: 
      2px 2px 0px var(--kidyland-blue, #0093f7),
      4px 4px 0px var(--kidyland-green, #3dad09),
      6px 6px 0px var(--kidyland-pink, #d30554),
      8px 8px 0px var(--kidyland-yellow, #ffce00),
      10px 10px 0px var(--kidyland-blue, #0093f7),
      12px 12px 0px var(--kidyland-green, #3dad09),
      14px 14px 0px var(--kidyland-pink, #d30554),
      16px 16px 0px var(--kidyland-yellow, #ffce00),
      18px 18px 0px var(--kidyland-blue, #0093f7);
  }
  
  /* Responsive adjustments */
  @media (max-width: 768px) {
    .title-md {
      --title-font-size: 3rem;
    }
    
    .title-lg {
      --title-font-size: 4rem;
    }
    
    .title-xl {
      --title-font-size: 5.5rem;
    }
    
    /* Reduce shadow layers on tablet for performance */
    :global(:root:not([data-theme="dark"])) .animated-title {
      text-shadow: 
        2px 2px 0px var(--kidyland-blue, #0093f7),
        4px 4px 0px var(--kidyland-green, #3dad09),
        6px 6px 0px var(--kidyland-pink, #d30554),
        8px 8px 0px var(--kidyland-yellow, #ffce00),
        10px 10px 0px var(--kidyland-blue, #0093f7),
        12px 12px 0px var(--kidyland-green, #3dad09);
    }
    
    :global([data-theme="dark"]) .animated-title {
      text-shadow: 
        2px 2px 0px var(--kidyland-blue, #0093f7),
        4px 4px 0px var(--kidyland-green, #3dad09),
        6px 6px 0px var(--kidyland-pink, #d30554),
        8px 8px 0px var(--kidyland-yellow, #ffce00),
        10px 10px 0px var(--kidyland-blue, #0093f7),
        12px 12px 0px var(--kidyland-green, #3dad09);
    }
  }
  
  @media (max-width: 480px) {
    .title-sm {
      --title-font-size: 2rem;
    }
    
    .title-md {
      --title-font-size: 2.5rem;
    }
    
    .title-lg {
      --title-font-size: 3rem;
    }
    
    .title-xl {
      --title-font-size: 4rem;
    }
    
    /* Reduce shadow layers on mobile for performance */
    :global(:root:not([data-theme="dark"])) .animated-title {
      text-shadow: 
        1px 1px 0px var(--kidyland-blue, #0093f7),
        2px 2px 0px var(--kidyland-green, #3dad09),
        3px 3px 0px var(--kidyland-pink, #d30554),
        4px 4px 0px var(--kidyland-yellow, #ffce00),
        5px 5px 0px var(--kidyland-blue, #0093f7);
    }
    
    :global([data-theme="dark"]) .animated-title {
      text-shadow: 
        1px 1px 0px var(--kidyland-blue, #0093f7),
        2px 2px 0px var(--kidyland-green, #3dad09),
        3px 3px 0px var(--kidyland-pink, #d30554),
        4px 4px 0px var(--kidyland-yellow, #ffce00),
        5px 5px 0px var(--kidyland-blue, #0093f7);
    }
  }
</style>
