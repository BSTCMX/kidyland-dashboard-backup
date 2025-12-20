<script lang="ts">
  /**
   * GeometricBackground - Optional subtle background effects (inspired by Beatcatalogue).
   * 
   * CSS-only particles for performance.
   * Can be disabled via prop for critical operations.
   * 
   * Props:
   * - enabled: boolean - Enable/disable effects (default: true)
   * - intensity: 'low' | 'medium' | 'high' - Effect intensity (default: 'low')
   */
  
  export let enabled: boolean = true;
  export let intensity: "low" | "medium" | "high" = "low";
  
  // Determine particle count based on intensity
  $: particleCount = intensity === "low" ? 3 : intensity === "medium" ? 5 : 8;
</script>

{#if enabled}
  <div class="geometric-background intensity-{intensity}">
    {#each Array(particleCount) as _, i}
      <div class="particle particle-{i}" style="--delay: {i * 0.5}s"></div>
    {/each}
  </div>
{/if}

<style>
  .geometric-background {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
  }
  
  .particle {
    position: absolute;
    border-radius: 50%;
    opacity: 0.1;
    animation: float 20s ease-in-out infinite;
    animation-delay: var(--delay);
    will-change: transform, opacity;
  }
  
  /* Low intensity - Subtle */
  .intensity-low .particle {
    width: 100px;
    height: 100px;
    background: radial-gradient(circle, rgba(0, 147, 247, 0.3) 0%, transparent 70%);
  }
  
  /* Medium intensity */
  .intensity-medium .particle {
    width: 150px;
    height: 150px;
    background: radial-gradient(circle, rgba(0, 147, 247, 0.4) 0%, transparent 70%);
  }
  
  /* High intensity */
  .intensity-high .particle {
    width: 200px;
    height: 200px;
    background: radial-gradient(circle, rgba(0, 147, 247, 0.5) 0%, transparent 70%);
  }
  
  /* Position particles */
  .particle-0 {
    top: 10%;
    left: 20%;
    background: radial-gradient(circle, rgba(0, 147, 247, 0.3) 0%, transparent 70%);
  }
  
  .particle-1 {
    top: 60%;
    left: 70%;
    background: radial-gradient(circle, rgba(61, 173, 9, 0.3) 0%, transparent 70%);
    animation-duration: 25s;
  }
  
  .particle-2 {
    top: 80%;
    left: 30%;
    background: radial-gradient(circle, rgba(0, 147, 247, 0.2) 0%, transparent 70%);
    animation-duration: 30s;
  }
  
  .particle-3 {
    top: 30%;
    left: 80%;
    background: radial-gradient(circle, rgba(61, 173, 9, 0.2) 0%, transparent 70%);
    animation-duration: 22s;
  }
  
  .particle-4 {
    top: 50%;
    left: 10%;
    background: radial-gradient(circle, rgba(0, 147, 247, 0.25) 0%, transparent 70%);
    animation-duration: 28s;
  }
  
  .particle-5 {
    top: 20%;
    left: 50%;
    background: radial-gradient(circle, rgba(61, 173, 9, 0.25) 0%, transparent 70%);
    animation-duration: 24s;
  }
  
  .particle-6 {
    top: 70%;
    left: 60%;
    background: radial-gradient(circle, rgba(0, 147, 247, 0.2) 0%, transparent 70%);
    animation-duration: 26s;
  }
  
  .particle-7 {
    top: 40%;
    left: 40%;
    background: radial-gradient(circle, rgba(61, 173, 9, 0.2) 0%, transparent 70%);
    animation-duration: 32s;
  }
  
  @keyframes float {
    0%, 100% {
      transform: translate(0, 0) scale(1);
      opacity: 0.1;
    }
    25% {
      transform: translate(30px, -30px) scale(1.1);
      opacity: 0.15;
    }
    50% {
      transform: translate(-20px, 20px) scale(0.9);
      opacity: 0.1;
    }
    75% {
      transform: translate(20px, 30px) scale(1.05);
      opacity: 0.12;
    }
  }
  
  /* Disable on mobile for performance */
  @media (max-width: 768px) {
    .geometric-background {
      display: none;
    }
  }
  
  /* Respect user's motion preferences */
  @media (prefers-reduced-motion: reduce) {
    .particle {
      animation: none;
      opacity: 0.05;
    }
  }
</style>

