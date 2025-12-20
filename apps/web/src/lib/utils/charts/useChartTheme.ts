/**
 * Chart theme utilities for reactive theme colors and responsive font sizes.
 * 
 * Provides reusable functions for Chart.js components to handle theme changes
 * and responsive font sizing. Follows Clean Architecture principles.
 */

export interface ChartThemeColors {
  textPrimary: string;
  textSecondary: string;
  bgCard: string;
  bgElevated: string;
  borderPrimary: string;
}

export interface FontSizeOptions {
  legend?: number;
  tooltipTitle?: number;
  tooltipBody?: number;
  axisTicks?: number;
}

export interface ResponsiveFontSizes {
  legend: number;
  tooltipTitle: number;
  tooltipBody: number;
  axisTicks: number;
}

/**
 * Get current theme colors from CSS variables.
 * This function reads CSS variables at call time, so it should be called
 * reactively when theme changes.
 */
export function getChartThemeColors(element?: HTMLElement): ChartThemeColors {
  if (typeof window === 'undefined') {
    // SSR fallback
    return {
      textPrimary: '#111827',
      textSecondary: '#6b7280',
      bgCard: '#ffffff',
      bgElevated: '#f9fafb',
      borderPrimary: '#e5e7eb',
    };
  }

  const root = element || document.documentElement;
  const computedStyle = getComputedStyle(root);

  return {
    textPrimary: computedStyle.getPropertyValue('--text-primary').trim() || '#111827',
    textSecondary: computedStyle.getPropertyValue('--text-secondary').trim() || '#6b7280',
    bgCard: computedStyle.getPropertyValue('--theme-bg-card').trim() || '#ffffff',
    bgElevated: computedStyle.getPropertyValue('--theme-bg-elevated').trim() || '#f9fafb',
    borderPrimary: computedStyle.getPropertyValue('--border-primary').trim() || '#e5e7eb',
  };
}

/**
 * Get responsive font sizes based on viewport width.
 * Desktop: larger fonts for better readability
 * Mobile: smaller fonts to fit screen
 */
export function getResponsiveFontSizes(customSizes?: FontSizeOptions): ResponsiveFontSizes {
  if (typeof window === 'undefined') {
    // SSR fallback - use desktop sizes
    return {
      legend: customSizes?.legend || 14,
      tooltipTitle: customSizes?.tooltipTitle || 16,
      tooltipBody: customSizes?.tooltipBody || 14,
      axisTicks: customSizes?.axisTicks || 12,
    };
  }

  const isMobile = window.innerWidth < 768;
  const isTablet = window.innerWidth >= 768 && window.innerWidth < 1024;

  if (isMobile) {
    return {
      legend: customSizes?.legend || 12,
      tooltipTitle: customSizes?.tooltipTitle || 14,
      tooltipBody: customSizes?.tooltipBody || 13,
      axisTicks: customSizes?.axisTicks || 11,
    };
  }

  if (isTablet) {
    return {
      legend: customSizes?.legend || 13,
      tooltipTitle: customSizes?.tooltipTitle || 15,
      tooltipBody: customSizes?.tooltipBody || 13,
      axisTicks: customSizes?.axisTicks || 11,
    };
  }

  // Desktop
  return {
    legend: customSizes?.legend || 14,
    tooltipTitle: customSizes?.tooltipTitle || 16,
    tooltipBody: customSizes?.tooltipBody || 14,
    axisTicks: customSizes?.axisTicks || 12,
  };
}

/**
 * Create a MutationObserver to watch for theme changes.
 * Returns a cleanup function to disconnect the observer.
 * 
 * @param callback Function to call when theme changes
 * @returns Cleanup function
 */
export function createThemeObserver(
  callback: () => void
): () => void {
  if (typeof window === 'undefined') {
    return () => {}; // No-op for SSR
  }

  const observer = new MutationObserver(() => {
    callback();
  });

  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme'],
  });

  return () => {
    observer.disconnect();
  };
}

/**
 * Check if colors have changed between two theme color objects.
 * Useful for preventing unnecessary chart updates.
 */
export function themeColorsChanged(
  oldColors: ChartThemeColors,
  newColors: ChartThemeColors
): boolean {
  return (
    oldColors.textPrimary !== newColors.textPrimary ||
    oldColors.textSecondary !== newColors.textSecondary ||
    oldColors.bgCard !== newColors.bgCard ||
    oldColors.bgElevated !== newColors.bgElevated ||
    oldColors.borderPrimary !== newColors.borderPrimary
  );
}



