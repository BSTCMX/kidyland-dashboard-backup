<script context="module" lang="ts">
  /**
   * Tab interface for ResponsiveTabs component.
   * Exported for use in parent components.
   */
  import type { ComponentType } from 'svelte';
  import type { SvelteComponent } from 'svelte';

  export interface Tab {
    id: string;
    label: string;
    icon: ComponentType<SvelteComponent>;
  }
</script>

<script lang="ts">
  /**
   * ResponsiveTabs - Responsive tabs navigation component.
   * 
   * Automatically switches between desktop tabs and mobile dropdown
   * based on viewport size. Maintains Clean Architecture principles.
   * 
   * Features:
   * - Desktop: Horizontal tabs (TabsDesktop)
   * - Mobile/Tablet: Dropdown menu (TabsMobile)
   * - Reactive breakpoint detection
   * - Accessible with ARIA attributes
   * - No hardcoded values
   */
  import { isMobileOrTablet } from '$lib/utils/useBreakpoint';
  import TabsDesktop from './TabsDesktop.svelte';
  import TabsMobile from './TabsMobile.svelte';

  export let tabs: Tab[] = [];
  export let activeTab: string = '';
  export let onTabChange: (tabId: string) => void = () => {};

  // Use breakpoint to determine if mobile/tablet
  // Mobile/Tablet: max-width 1024px uses dropdown
  // Desktop: min-width 1025px uses horizontal tabs
  $: useMobile = $isMobileOrTablet;
</script>

<div class="responsive-tabs-container">
  {#if useMobile}
    <TabsMobile {tabs} {activeTab} {onTabChange} />
  {:else}
    <TabsDesktop {tabs} {activeTab} {onTabChange} />
  {/if}
</div>

<style>
  .responsive-tabs-container {
    width: 100%;
  }
</style>

