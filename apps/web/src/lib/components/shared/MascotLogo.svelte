<script lang="ts">
  /**
   * MascotLogo component - Displays mascot logo.
   * 
   * Simple component for displaying mascot/logo images.
   */
  export let src: string = "/logo.svg";
  export let alt: string = "Kidyland Mascot";
  export let size: "sm" | "md" | "lg" = "md";
</script>

<div class="mascot-logo mascot-logo-{size}">
  <img 
    src={src} 
    alt={alt}
    class="mascot-image"
    loading="lazy"
  />
</div>

<style>
  .mascot-logo {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .mascot-image {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }

  .mascot-logo-sm {
    width: 48px;
    height: 48px;
  }

  .mascot-logo-md {
    width: 64px;
    height: 64px;
  }

  .mascot-logo-lg {
    width: 96px;
    height: 96px;
  }
</style>
