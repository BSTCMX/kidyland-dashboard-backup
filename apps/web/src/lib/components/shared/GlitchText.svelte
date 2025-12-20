<script lang="ts">
  /**
   * GlitchText - Text with glitch effect (inspired by Beatcatalogue + Kidyland colors).
   * 
   * Features:
   * - Glitch animation on hover
   * - Glow effects with Kidyland colors
   * - Auto glitch every 5-8 seconds
   */
  
  export let text: string;
  export let tag: "h1" | "h2" | "p" = "h1";
  export let autoGlitch: boolean = true;
  
  let glitchActive = false;
  
  function triggerGlitch() {
    glitchActive = true;
    setTimeout(() => (glitchActive = false), 300);
  }
  
  // Auto glitch every 5-8 seconds
  if (autoGlitch && typeof setInterval !== "undefined") {
    setInterval(() => {
      if (Math.random() > 0.6) triggerGlitch();
    }, 6000);
  }
</script>

<svelte:element
  this={tag}
  class="glitch-text"
  class:glitch-active={glitchActive}
  data-text={text}
  on:mouseenter={triggerGlitch}
  role="heading"
>
  {text}
</svelte:element>

<style>
  .glitch-text {
    position: relative;
    display: inline-block;
    font-family: var(--font-primary);
    color: var(--text-primary);
    transition: all 0.3s;
    text-shadow:
      0 0 5px rgba(0, 147, 247, 0),
      0 0 10px rgba(61, 173, 9, 0);
  }
  
  /* Glow en hover - Kidyland colors */
  .glitch-text:hover {
    text-shadow:
      0 0 10px rgba(0, 147, 247, 0.6),
      0 0 20px rgba(61, 173, 9, 0.4),
      0 0 30px rgba(0, 147, 247, 0.3);
    transform: scale(1.02);
  }
  
  .glitch-text.glitch-active {
    animation: glitch 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    text-shadow:
      0 0 20px rgba(0, 147, 247, 0.8),
      0 0 40px rgba(61, 173, 9, 0.6),
      0 0 60px rgba(0, 147, 247, 0.4) !important;
  }
  
  .glitch-text.glitch-active::before,
  .glitch-text.glitch-active::after {
    content: attr(data-text);
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    opacity: 0.8;
  }
  
  .glitch-text.glitch-active::before {
    animation: glitch-1 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    color: transparent;
    text-shadow:
      -2px 0 0 #0093f7,
      0 0 10px #0093f7,
      0 0 20px #0093f7;
    z-index: -1;
  }
  
  .glitch-text.glitch-active::after {
    animation: glitch-2 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    color: transparent;
    text-shadow:
      2px 0 0 #3dad09,
      0 0 10px #3dad09,
      0 0 20px #3dad09;
    z-index: -2;
  }
  
  @keyframes glitch {
    0%, 100% {
      transform: translate(0);
    }
    20% {
      transform: translate(-2px, 2px);
    }
    40% {
      transform: translate(-2px, -2px);
    }
    60% {
      transform: translate(2px, 2px);
    }
    80% {
      transform: translate(2px, -2px);
    }
  }
  
  @keyframes glitch-1 {
    0%, 100% {
      transform: translate(0);
      opacity: 0;
    }
    50% {
      transform: translate(-3px, 2px);
      opacity: 1;
    }
  }
  
  @keyframes glitch-2 {
    0%, 100% {
      transform: translate(0);
      opacity: 0;
    }
    50% {
      transform: translate(3px, -2px);
      opacity: 1;
    }
  }
  
  /* Responsive */
  @media (max-width: 768px) {
    .glitch-text:hover {
      transform: scale(1);
    }
  }
</style>



