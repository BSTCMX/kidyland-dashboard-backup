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

<div class="animated-title title-{size}">
  {text}
</div>

<style>
  @import url('https://fonts.googleapis.com/css2?family=Niconne&display=swap');
  
  .animated-title {
    font-family: 'Niconne', var(--font-primary, system-ui, sans-serif);
    font-size: var(--title-font-size, 8rem);
    font-weight: 700;
    text-align: center;
    height: auto;
    line-height: 1.2;
    color: var(--text-primary, #fcedd8);
    margin: var(--spacing-lg) auto var(--spacing-sm);
    position: relative;
    padding: var(--spacing-xl) 0;
    
    /* Layered text-shadow using Kidyland color palette */
    /* Colors: blue (#0093f7), green (#3dad09), pink (#d30554), yellow (#ffce00) */
    text-shadow: 
      5px 5px 0px var(--kidyland-blue, #0093f7),
      10px 10px 0px var(--kidyland-green, #3dad09),
      15px 15px 0px var(--kidyland-pink, #d30554),
      20px 20px 0px var(--kidyland-yellow, #ffce00),
      25px 25px 0px var(--kidyland-blue, #0093f7),
      30px 30px 0px var(--kidyland-green, #3dad09),
      35px 35px 0px var(--kidyland-pink, #d30554),
      40px 40px 0px var(--kidyland-yellow, #ffce00),
      45px 45px 0px var(--kidyland-blue, #0093f7);
    
    /* Smooth transitions for theme changes */
    transition: color 0.3s ease, text-shadow 0.3s ease;
  }
  
  /* Size variants - adapted for login page */
  .title-sm {
    --title-font-size: 4rem;
  }
  
  .title-md {
    --title-font-size: 6rem;
  }
  
  .title-lg {
    --title-font-size: 8rem;
  }
  
  .title-xl {
    --title-font-size: 12rem;
  }
  
  /* Dark mode adjustments - maintain color palette */
  :global([data-theme="dark"]) .animated-title {
    color: var(--text-primary, #fcedd8);
    /* Same shadow effect, colors remain vibrant in dark mode */
  }
  
  /* Light mode adjustments */
  :global(:root:not([data-theme="dark"])) .animated-title {
    color: var(--text-primary, #0f172a);
    /* Slightly reduced shadow intensity for better contrast in light mode */
    text-shadow: 
      3px 3px 0px var(--kidyland-blue, #0093f7),
      6px 6px 0px var(--kidyland-green, #3dad09),
      9px 9px 0px var(--kidyland-pink, #d30554),
      12px 12px 0px var(--kidyland-yellow, #ffce00),
      15px 15px 0px var(--kidyland-blue, #0093f7),
      18px 18px 0px var(--kidyland-green, #3dad09),
      21px 21px 0px var(--kidyland-pink, #d30554),
      24px 24px 0px var(--kidyland-yellow, #ffce00),
      27px 27px 0px var(--kidyland-blue, #0093f7);
  }
  
  /* Responsive adjustments */
  @media (max-width: 768px) {
    .title-lg {
      --title-font-size: 5rem;
    }
    
    .title-xl {
      --title-font-size: 7rem;
    }
    
    /* Reduce shadow layers on tablet for performance */
    .animated-title {
      text-shadow: 
        3px 3px 0px var(--kidyland-blue, #0093f7),
        6px 6px 0px var(--kidyland-green, #3dad09),
        9px 9px 0px var(--kidyland-pink, #d30554),
        12px 12px 0px var(--kidyland-yellow, #ffce00),
        15px 15px 0px var(--kidyland-blue, #0093f7),
        18px 18px 0px var(--kidyland-green, #3dad09);
    }
  }
  
  @media (max-width: 480px) {
    .title-lg {
      --title-font-size: 3.5rem;
    }
    
    .title-xl {
      --title-font-size: 5rem;
    }
    
    /* Reduce shadow layers on mobile for performance */
    .animated-title {
      text-shadow: 
        2px 2px 0px var(--kidyland-blue, #0093f7),
        4px 4px 0px var(--kidyland-green, #3dad09),
        6px 6px 0px var(--kidyland-pink, #d30554),
        8px 8px 0px var(--kidyland-yellow, #ffce00),
        10px 10px 0px var(--kidyland-blue, #0093f7);
    }
  }
</style>
