/**
 * Chart configuration utilities for Chart.js.
 * 
 * Provides base configuration, themes, and helpers for consistent chart styling
 * across the application. Follows Clean Architecture principles.
 */
import type { ChartConfiguration, ChartData, ChartOptions } from 'chart.js';
import type { ChartThemeColors, ResponsiveFontSizes } from './useChartTheme';

/**
 * Get CSS variable value from computed styles.
 */
function getCSSVariable(variable: string, element?: HTMLElement): string {
  if (typeof window === 'undefined') return '';
  
  const el = element || document.documentElement;
  return getComputedStyle(el).getPropertyValue(variable).trim();
}

/**
 * Chart theme colors based on application CSS variables.
 */
export function getChartTheme(element?: HTMLElement) {
  return {
    primary: getCSSVariable('--accent-primary', element) || '#0093F7',
    secondary: getCSSVariable('--accent-secondary', element) || '#00C9FF',
    success: getCSSVariable('--success-color', element) || '#10B981',
    warning: getCSSVariable('--warning-color', element) || '#F59E0B',
    error: getCSSVariable('--error-color', element) || '#EF4444',
    textPrimary: getCSSVariable('--text-primary', element) || '#FFFFFF',
    textSecondary: getCSSVariable('--text-secondary', element) || '#9CA3AF',
    bgCard: getCSSVariable('--theme-bg-card', element) || '#1F2937',
    bgElevated: getCSSVariable('--theme-bg-elevated', element) || '#374151',
    borderPrimary: getCSSVariable('--border-primary', element) || '#4B5563',
  };
}

/**
 * Base chart options with responsive and accessibility settings.
 * 
 * @param element Optional HTML element to read CSS variables from
 * @param themeColors Optional theme colors (if not provided, will read from CSS)
 * @param fontSizes Optional font sizes (if not provided, will use defaults)
 */
export function getBaseChartOptions(
  element?: HTMLElement,
  themeColors?: ChartThemeColors,
  fontSizes?: ResponsiveFontSizes
): ChartOptions {
  const theme = themeColors || getChartTheme(element);
  const fonts = fontSizes || {
    legend: 12,
    tooltipTitle: 14,
    tooltipBody: 12,
    axisTicks: 11,
  };
  
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          color: theme.textSecondary,
          font: {
            size: fonts.legend,
            family: 'var(--font-primary, system-ui, sans-serif)',
          },
          padding: 12,
          usePointStyle: true,
        },
      },
      tooltip: {
        backgroundColor: theme.bgElevated,
        titleColor: theme.textPrimary,
        bodyColor: theme.textSecondary,
        borderColor: theme.borderPrimary,
        borderWidth: 1,
        padding: 12,
        cornerRadius: 8,
        displayColors: true,
        titleFont: {
          size: fonts.tooltipTitle,
          weight: '600',
          family: 'var(--font-primary, system-ui, sans-serif)',
        },
        bodyFont: {
          size: fonts.tooltipBody,
          family: 'var(--font-primary, system-ui, sans-serif)',
        },
        callbacks: {
          label: function(context) {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            
            // Format currency values
            if (label.toLowerCase().includes('revenue') || label.toLowerCase().includes('ventas')) {
              return `${label}: $${(value / 100).toFixed(2)}`;
            }
            
            return `${label}: ${value}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: {
          color: theme.borderPrimary,
          drawBorder: false,
        },
        ticks: {
          color: theme.textSecondary,
          font: {
            size: fonts.axisTicks,
            family: 'var(--font-primary, system-ui, sans-serif)',
          },
        },
      },
      y: {
        grid: {
          color: theme.borderPrimary,
          drawBorder: false,
        },
        ticks: {
          color: theme.textSecondary,
          font: {
            size: fonts.axisTicks,
            family: 'var(--font-primary, system-ui, sans-serif)',
          },
          callback: function(value) {
            // Format currency values on Y axis
            return `$${(Number(value) / 100).toFixed(0)}`;
          },
        },
      },
    },
  };
}

/**
 * Create a time series chart configuration.
 * 
 * @param data Chart data
 * @param element Optional HTML element to read CSS variables from
 * @param themeColors Optional theme colors (if not provided, will read from CSS)
 * @param fontSizes Optional font sizes (if not provided, will use defaults)
 */
export function createTimeSeriesConfig(
  data: ChartData<'line'>,
  element?: HTMLElement,
  themeColors?: ChartThemeColors,
  fontSizes?: ResponsiveFontSizes
): ChartConfiguration<'line'> {
  const baseOptions = getBaseChartOptions(element, themeColors, fontSizes);
  
  return {
    type: 'line',
    data,
    options: {
      ...baseOptions,
      interaction: {
        intersect: false,
        mode: 'index',
      },
      elements: {
        point: {
          radius: 4,
          hoverRadius: 6,
          borderWidth: 2,
        },
        line: {
          tension: 0.4,
          borderWidth: 2,
        },
      },
      plugins: {
        ...baseOptions.plugins,
        legend: {
          ...baseOptions.plugins?.legend,
          display: true,
        },
      },
    },
  };
}

/**
 * Create a bar chart configuration.
 * 
 * @param data Chart data
 * @param element Optional HTML element to read CSS variables from
 * @param themeColors Optional theme colors (if not provided, will read from CSS)
 * @param fontSizes Optional font sizes (if not provided, will use defaults)
 */
export function createBarChartConfig(
  data: ChartData<'bar'>,
  element?: HTMLElement,
  themeColors?: ChartThemeColors,
  fontSizes?: ResponsiveFontSizes
): ChartConfiguration<'bar'> {
  const baseOptions = getBaseChartOptions(element, themeColors, fontSizes);
  
  return {
    type: 'bar',
    data,
    options: {
      ...baseOptions,
      plugins: {
        ...baseOptions.plugins,
        legend: {
          ...baseOptions.plugins?.legend,
          display: true,
        },
      },
    },
  };
}

/**
 * Create a pie/doughnut chart configuration.
 * 
 * @param data Chart data
 * @param element Optional HTML element to read CSS variables from
 * @param themeColors Optional theme colors (if not provided, will read from CSS)
 * @param fontSizes Optional font sizes (if not provided, will use defaults)
 */
export function createPieChartConfig(
  data: ChartData<'pie'>,
  element?: HTMLElement,
  themeColors?: ChartThemeColors,
  fontSizes?: ResponsiveFontSizes
): ChartConfiguration<'pie'> {
  const baseOptions = getBaseChartOptions(element, themeColors, fontSizes);
  
  return {
    type: 'pie',
    data,
    options: {
      ...baseOptions,
      plugins: {
        ...baseOptions.plugins,
        legend: {
          ...baseOptions.plugins?.legend,
          position: 'right',
        },
      },
    },
  };
}

