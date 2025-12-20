<script lang="ts">
  /**
   * Logo Component - Reusable component for displaying Kidyland logo.
   * 
   * Displays the logo with optional glow effect (inspired by Databoard).
   * Horizontal logo (800x400) - says "Kidyland"
   * 
   * Props:
   * - size: 'sm' | 'md' | 'lg' | 'xl' - Logo size
   * - variant: 'default' | 'glow' - Style variant
   * - showGlow: boolean - Enable glow effect (default: true for variant="glow")
   */
  
  export let size: "sm" | "md" | "lg" | "xl" = "md";
  export let variant: "default" | "glow" = "default";
  export let showGlow: boolean = variant === "glow";
  
  // Logo path (configurable)
  const LOGO_IMAGE_PATH = "/logo.svg";
  
  // Determine if glow should be shown
  $: displayGlow = variant === "glow" && showGlow;
</script>

<div 
  class="logo-container logo-{size} logo-{variant}"
  class:has-glow={displayGlow}
>
  <img 
    src={LOGO_IMAGE_PATH} 
    alt="Kidyland Logo"
    class="logo-image"
    loading="lazy"
  />
</div>

<style>
  .logo-container {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .logo-image {
    width: 100%;
    height: 100%;
    object-fit: contain;
    display: block;
  }
  
  /* Size variants - Horizontal logo (800x400 = 2:1 ratio) */
  .logo-sm {
    width: 120px;
    height: 60px; /* 2:1 ratio */
  }
  
  .logo-md {
    width: 160px;
    height: 80px; /* 2:1 ratio */
  }
  
  .logo-lg {
    width: 240px;
    height: 120px; /* 2:1 ratio */
  }
  
  .logo-xl {
    width: 320px;
    height: 160px; /* 2:1 ratio */
  }
  
  /* Glow effect (inspired by Databoard with Kidyland colors) */
  .logo-container.has-glow {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(240, 240, 255, 0.9) 100%);
    padding: 8px;
    border-radius: 16px;
    box-shadow:
      0 0 16px rgba(0, 147, 247, 0.5),  /* Kidyland blue */
      0 0 32px rgba(61, 173, 9, 0.3);    /* Kidyland green */
    border: 2px solid rgba(255, 255, 255, 0.3);
  }
  
  /* Larger glow for bigger sizes */
  .logo-lg.has-glow,
  .logo-xl.has-glow {
    padding: 12px;
    border-radius: 22px;
    box-shadow:
      0 0 20px rgba(0, 147, 247, 0.6),
      0 0 40px rgba(61, 173, 9, 0.4),
      0 0 60px rgba(0, 147, 247, 0.2);
  }
  
  /* Default variant (no glow) */
  .logo-default {
    /* No additional styling */
  }
  
  /* Hover effect */
  .logo-container:hover {
    transform: scale(1.02);
  }
  
  /* Responsive */
  @media (max-width: 768px) {
    .logo-lg {
      width: 200px;
      height: 100px;
    }
    
    .logo-xl {
      width: 240px;
      height: 120px;
    }
  }
</style>
