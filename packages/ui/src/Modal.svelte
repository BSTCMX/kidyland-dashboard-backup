<script lang="ts">
  /**
   * Modal component - Codrops pattern implementation
   * Overlay and modal as siblings, centered with transform
   * Follows Svelte "props down, events up" pattern.
   */
  import { X } from "lucide-svelte";
  import { onMount } from "svelte";
  import { createEventDispatcher } from "svelte";
  
  export let open = false;
  export let title: string = "";
  export let size: "sm" | "md" | "lg" | "xl" = "md";
  export let anchorPosition: { top: number; left: number } | null = null;
  
  const dispatch = createEventDispatcher<{
    close: null;
  }>();
  
  // Breakpoints profesionales 2025
  let sizeClasses = {
    sm: "max-w-md",        // 448px
    md: "max-w-2xl",       // 672px
    lg: "max-w-4xl",       // 896px
    xl: "max-w-6xl",       // 1152px
  };
  
  let windowWidth = 1024;
  let windowHeight = 768;
  
  onMount(() => {
    if (typeof window !== 'undefined') {
      windowWidth = window.innerWidth;
      windowHeight = window.innerHeight;
      
      const handleResize = () => {
        windowWidth = window.innerWidth;
        windowHeight = window.innerHeight;
      };
      
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
    }
    return undefined;
  });
  
  // Calculate modal position: centered by default, positioned by anchor on desktop
  $: useAnchorPosition = anchorPosition && windowWidth > 768; // Only use anchor on desktop
  
  $: modalStyle = useAnchorPosition && anchorPosition ? (() => {
    const modalWidth = size === 'lg' ? 672 : size === 'xl' ? 1152 : size === 'md' ? 672 : 448;
    const modalMaxHeight = 600; // Altura máxima estimada para formularios largos
    const spacing = 20;
    
    // Position modal below and to the right of button
    let top = anchorPosition.top + 30; // Add spacing below button
    let left = anchorPosition.left;
    
    // Adjust if modal goes outside viewport horizontally
    if (left + modalWidth > windowWidth) {
      left = Math.max(spacing, windowWidth - modalWidth - spacing);
    }
    if (left < spacing) {
      left = spacing;
    }
    
    // Calculate available space below and above
    const spaceBelow = windowHeight - anchorPosition.top;
    const spaceAbove = anchorPosition.top;
    
    // If there's not enough space below, try to position above
    if (spaceBelow < modalMaxHeight && spaceAbove > spaceBelow) {
      // Position above button
      top = Math.max(spacing, anchorPosition.top - modalMaxHeight - spacing);
    } else if (top + modalMaxHeight > windowHeight) {
      // If still doesn't fit, center it vertically in viewport
      top = Math.max(spacing, (windowHeight - modalMaxHeight) / 2);
    }
    if (top < spacing) {
      top = spacing;
    }
    
    return `top: ${top}px; left: ${left}px; transform: none;`;
  })() : '';
  
  $: showClass = open ? "md-show" : "";
  
  // FIXED: Use event dispatcher instead of modifying prop directly
  function handleClose() {
    dispatch('close');
  }
  
  function handleOverlayClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      handleClose();
    }
  }
  
  function handleEscape(event: KeyboardEvent) {
    if (event.key === "Escape") {
      handleClose();
    }
  }
</script>

<svelte:window on:keydown={handleEscape} />

<!-- Modal - Codrops pattern: modal and overlay as siblings -->
<div
  class="md-modal {showClass}"
  class:md-effect-anchor={useAnchorPosition}
  style={useAnchorPosition && anchorPosition ? modalStyle : ''}
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
  aria-hidden={!open}
>
  <!-- Modal Content -->
  <div
    class="md-content {sizeClasses[size]}"
    style="max-height: 90vh; max-height: 90dvh;"
    on:click|stopPropagation
  >
    <!-- Close button -->
    <button
      type="button"
      class="md-close"
      on:click={handleClose}
      aria-label="Cerrar modal"
    >
      <X size={20} strokeWidth={2} />
    </button>

    <!-- Header -->
    {#if title}
      <div class="modal-header">
        <h3 id="modal-title">{title}</h3>
      </div>
    {/if}
    
    <!-- Content -->
    <div class="modal-content">
      <slot />
    </div>
    
    <!-- Footer (optional) -->
    {#if $$slots.footer}
      <div class="modal-footer">
        <slot name="footer" />
      </div>
    {/if}
  </div>
</div>

<!-- Overlay - Separate sibling element (Codrops pattern) -->
<div
  class="md-overlay {showClass}"
  on:click={handleOverlayClick}
  role="presentation"
></div>

<style>
  /* Codrops Modal Pattern */
  .md-modal {
    position: fixed;
    width: 50%;
    max-width: 630px;
    min-width: 320px;
    height: auto;
    z-index: 2000;
    visibility: hidden;
    backface-visibility: hidden;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
  }

  .md-modal.md-show {
    visibility: visible;
  }

  .md-content {
    position: relative;
    background: var(--theme-bg-elevated, #fff);
    color: var(--text-primary);
    border-radius: 8px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    width: 100%;
    /* Modern viewport units with fallback for older browsers */
    max-height: 90vh; /* Fallback for browsers that don't support dvh */
    max-height: 90dvh; /* Dynamic viewport height - respects mobile browser bars */
    /* Flexbox layout for proper space distribution */
    display: flex;
    flex-direction: column;
    /* Hide overflow - let .modal-content handle scroll */
    overflow: hidden;
  }

  /* Anchor positioning - override default centering */
  .md-modal.md-effect-anchor {
    width: auto;
    min-width: 320px;
    transform: none; /* Remove default centering transform */
  }

  /* Overlay */
  .md-overlay {
    position: fixed;
    width: 100%;
    height: 100%;
    visibility: hidden;
    top: 0;
    left: 0;
    z-index: 1000;
    opacity: 0;
    background: rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(2px);
    -webkit-backdrop-filter: blur(2px);
    transition: all 0.3s;
  }

  .md-show ~ .md-overlay {
    opacity: 1;
    visibility: visible;
  }

  /* Modal animations */
  .md-content {
    opacity: 0;
    transform: scale(0.7);
    transition: all 0.3s;
  }

  .md-show .md-content {
    opacity: 1;
    transform: scale(1);
  }

  /* When using anchor, don't scale transform, just fade */
  .md-modal.md-effect-anchor .md-content {
    transform: scale(1);
  }

  .md-modal.md-effect-anchor.md-show .md-content {
    opacity: 1;
    transform: scale(1);
  }

  /* Close button */
  .md-close {
    position: absolute;
    top: 1rem;
    right: 1rem;
    z-index: 50;
    width: 2.5rem;
    height: 2.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: var(--theme-bg-secondary, #f8fafc);
    border: 1px solid var(--border-primary, #e5e7eb);
    color: var(--text-primary, #1f2029);
    cursor: pointer;
    transition: all 200ms;
  }

  .md-close:hover {
    transform: scale(1.1);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  /* Header */
  .modal-header {
    padding: 1.5rem;
    padding-top: 3rem;
    border-bottom: 1px solid var(--border-primary, #e5e7eb);
    text-align: center;
    flex-shrink: 0; /* Prevent header from shrinking */
  }

  .modal-header h3 {
    font-size: 1.25rem;
    font-weight: bold;
    color: var(--text-primary, #1f2029);
    margin: 0;
  }

  /* Content */
  .modal-content {
    padding: 1.5rem;
    /* Flexbox: grow to fill available space, allow scroll */
    flex: 1;
    min-height: 0; /* Critical: allows scroll in flex children */
    overflow-y: auto;
    /* Touch scrolling optimizations for mobile */
    touch-action: pan-y; /* Enable vertical touch scrolling */
    -webkit-overflow-scrolling: touch; /* Smooth scrolling on iOS Safari */
    /* Dynamic height calculated by flexbox, no fixed max-height needed */
  }

  /* Footer */
  .modal-footer {
    padding: 1.5rem;
    border-top: 1px solid var(--border-primary, #e5e7eb);
    background: var(--theme-bg-secondary, #f8fafc);
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 0.75rem;
    flex-shrink: 0; /* Prevent footer from shrinking */
  }

  /* Responsive - Mobile */
  @media screen and (max-width: 768px) {
    .md-modal {
      width: calc(100vw - 2rem);
      max-width: calc(100vw - 2rem);
      min-width: auto;
      top: 50% !important;
      left: 50% !important;
      transform: translate(-50%, -50%) !important;
    }

    .md-modal.md-effect-anchor .md-content {
      position: relative !important;
      top: auto !important;
      left: auto !important;
      transform: none !important;
    }

    /* Adjust max-height for mobile to account for browser bars and safe areas */
    .md-content {
      max-height: calc(100vh - 4rem); /* Fallback for older browsers */
      max-height: calc(100dvh - 4rem); /* Modern: respects mobile browser UI */
    }

    .modal-header {
      padding: 1rem;
      padding-top: 2.5rem; /* Reduce top padding on mobile */
      flex-shrink: 0;
    }

    .modal-content {
      padding: 1rem;
      /* Ensure scroll works on mobile - flexbox handles height */
      min-height: 0;
      /* Explicitly enable scroll with touch support */
      overflow-y: auto;
      overflow-x: hidden;
      touch-action: pan-y;
      -webkit-overflow-scrolling: touch;
    }
  }
</style>
