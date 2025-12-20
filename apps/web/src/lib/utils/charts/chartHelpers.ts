/**
 * Chart helper functions for data transformation.
 * 
 * Utilities for transforming backend data into Chart.js format.
 */

/**
 * Format date for chart labels.
 */
export function formatDateLabel(date: string | Date, format: 'day' | 'week' | 'month' = 'day'): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  
  if (format === 'day') {
    return d.toLocaleDateString('es-ES', { day: '2-digit', month: 'short' });
  } else if (format === 'week') {
    return `Sem ${d.toLocaleDateString('es-ES', { week: 'numeric' })}`;
  } else {
    return d.toLocaleDateString('es-ES', { month: 'short', year: 'numeric' });
  }
}

/**
 * Format currency for chart tooltips.
 */
export function formatCurrency(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`;
}

/**
 * Generate color palette for charts.
 */
export function generateColorPalette(count: number, element?: HTMLElement): string[] {
  const colors = [
    '#0093F7', // Primary blue
    '#00C9FF', // Secondary blue
    '#10B981', // Success green
    '#F59E0B', // Warning orange
    '#EF4444', // Error red
    '#8B5CF6', // Purple
    '#EC4899', // Pink
    '#14B8A6', // Teal
  ];
  
  // Repeat colors if needed
  const palette: string[] = [];
  for (let i = 0; i < count; i++) {
    palette.push(colors[i % colors.length]);
  }
  
  return palette;
}

/**
 * Transform time series data for Chart.js.
 */
export interface TimeSeriesDataPoint {
  date: string;
  revenue_cents: number;
  sales_count?: number;
  atv_cents?: number;
}

export function transformTimeSeriesData(
  data: TimeSeriesDataPoint[],
  metric: 'revenue' | 'sales_count' | 'atv' = 'revenue'
): { labels: string[]; datasets: any[] } {
  const labels = data.map(point => formatDateLabel(point.date, 'day'));
  
  let values: number[];
  let label: string;
  let color: string;
  
  if (metric === 'revenue') {
    values = data.map(point => point.revenue_cents);
    label = 'Revenue';
    color = '#0093F7';
  } else if (metric === 'sales_count') {
    values = data.map(point => point.sales_count || 0);
    label = 'Ventas';
    color = '#10B981';
  } else {
    values = data.map(point => point.atv_cents || 0);
    label = 'Ticket Promedio';
    color = '#F59E0B';
  }
  
  return {
    labels,
    datasets: [
      {
        label,
        data: values,
        borderColor: color,
        backgroundColor: `${color}40`, // 40 = 25% opacity in hex
        fill: true,
        tension: 0.4,
      },
    ],
  };
}

/**
 * Transform grouped data for bar charts.
 */
export interface GroupedDataPoint {
  label: string;
  value: number;
  color?: string;
}

export function transformGroupedData(
  data: GroupedDataPoint[],
  label: string = 'Valor'
): { labels: string[]; datasets: any[] } {
  const labels = data.map(point => point.label);
  const values = data.map(point => point.value);
  const colors = data.map((point, index) => 
    point.color || generateColorPalette(data.length)[index]
  );
  
  return {
    labels,
    datasets: [
      {
        label,
        data: values,
        backgroundColor: colors,
        borderColor: colors.map(c => c + 'CC'), // Add opacity
        borderWidth: 1,
      },
    ],
  };
}

/**
 * Transform arqueos time series data for Chart.js.
 */
export interface ArqueosTimeSeriesDataPoint {
  date: string;
  system_total_cents: number;
  physical_count_cents: number;
  difference_cents: number;
  arqueos_count: number;
  perfect_matches: number;
  discrepancies: number;
}

export function transformArqueosTimeSeriesData(
  data: ArqueosTimeSeriesDataPoint[],
  metric: 'difference' | 'system' | 'physical' | 'discrepancies' = 'difference'
): { labels: string[]; datasets: any[] } {
  const labels = data.map(point => formatDateLabel(point.date, 'day'));
  
  let values: number[];
  let label: string;
  let color: string;
  
  if (metric === 'difference') {
    values = data.map(point => point.difference_cents);
    label = 'Diferencia';
    color = '#EF4444'; // Red for differences
  } else if (metric === 'system') {
    values = data.map(point => point.system_total_cents);
    label = 'Sistema';
    color = '#0093F7'; // Blue for system
  } else if (metric === 'physical') {
    values = data.map(point => point.physical_count_cents);
    label = 'Físico';
    color = '#10B981'; // Green for physical
  } else {
    values = data.map(point => point.discrepancies);
    label = 'Discrepancias';
    color = '#F59E0B'; // Orange for discrepancies
  }
  
  return {
    labels,
    datasets: [
      {
        label,
        data: values,
        borderColor: color,
        backgroundColor: `${color}40`, // 40 = 25% opacity in hex
        fill: true,
        tension: 0.4,
      },
    ],
  };
}

/**
 * Transform inventory time series data for Chart.js.
 */
export interface InventoryTimeSeriesDataPoint {
  date: string;
  stock_qty: number;
  products_count: number;
  low_stock_count: number;
  total_value_cents: number;
}

export function transformInventoryTimeSeriesData(
  data: InventoryTimeSeriesDataPoint[],
  metric: 'stock_qty' | 'total_value' | 'low_stock_count' = 'stock_qty'
): { labels: string[]; datasets: any[] } {
  const labels = data.map(point => formatDateLabel(point.date, 'day'));
  
  let values: number[];
  let label: string;
  let color: string;
  
  if (metric === 'stock_qty') {
    values = data.map(point => point.stock_qty);
    label = 'Cantidad de Stock';
    color = '#0093F7'; // Blue
  } else if (metric === 'total_value') {
    values = data.map(point => point.total_value_cents);
    label = 'Valor Total';
    color = '#10B981'; // Green
  } else {
    values = data.map(point => point.low_stock_count);
    label = 'Productos con Stock Bajo';
    color = '#EF4444'; // Red
  }
  
  return {
    labels,
    datasets: [
      {
        label,
        data: values,
        borderColor: color,
        backgroundColor: `${color}40`,
        fill: true,
        tension: 0.4,
      },
    ],
  };
}

/**
 * Transform services time series data for Chart.js.
 */
export interface ServicesTimeSeriesDataPoint {
  date: string;
  service_sales_count: number;
  package_sales_count: number;
  total_sales_count: number;
  revenue_cents: number;
  active_timers_count: number;
}

export function transformServicesTimeSeriesData(
  data: ServicesTimeSeriesDataPoint[],
  metric: 'revenue' | 'total_sales' | 'active_timers' = 'revenue'
): { labels: string[]; datasets: any[] } {
  const labels = data.map(point => formatDateLabel(point.date, 'day'));
  
  let values: number[];
  let label: string;
  let color: string;
  
  if (metric === 'revenue') {
    values = data.map(point => point.revenue_cents);
    label = 'Revenue';
    color = '#0093F7'; // Blue
  } else if (metric === 'total_sales') {
    values = data.map(point => point.total_sales_count);
    label = 'Ventas Totales';
    color = '#10B981'; // Green
  } else {
    values = data.map(point => point.active_timers_count);
    label = 'Timers Activos';
    color = '#F59E0B'; // Orange
  }
  
  return {
    labels,
    datasets: [
      {
        label,
        data: values,
        borderColor: color,
        backgroundColor: `${color}40`,
        fill: true,
        tension: 0.4,
      },
    ],
  };
}

