<script lang="ts">
  import { onMount } from "svelte";

  let wakeLock: any = null;

  onMount(async () => {
    // Request wake lock to keep screen awake (for kiosk/display mode)
    if ('wakeLock' in navigator) {
      try {
        wakeLock = await (navigator as any).wakeLock.request('screen');
        console.log('[Display] Wake lock activated - screen will stay awake');
      } catch (err) {
        console.warn('[Display] Wake lock not available:', err);
      }
    }

    // Release wake lock on unmount
    return () => {
      if (wakeLock) {
        wakeLock.release();
        console.log('[Display] Wake lock released');
      }
    };
  });
</script>

<div class="display-layout">
  <slot />
</div>

<style>
  .display-layout {
    width: 100vw;
    height: 100dvh; /* Dynamic viewport height - excludes browser bars */
    height: 100vh; /* Fallback for older browsers */
    overflow: hidden;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    color: var(--text-primary);
    position: relative;
  }

  /* Ensure no scrollbars */
  :global(body) {
    overflow: hidden;
  }
</style>
