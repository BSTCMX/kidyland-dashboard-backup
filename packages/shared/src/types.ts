export interface User {
  id: string;
  username: string;
  name: string;
  role:
    | "super_admin"
    | "admin_viewer"
    | "recepcion"
    | "kidibar"
    | "monitor";
  is_active: boolean;
  sucursal_id: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  last_login: string | null;
}

export interface ChildInfo {
  name: string;
  age?: number | null;
}

export interface Sale {
  id: string;
  sucursal_id: string;
  usuario_id: string;
  tipo: "service" | "day" | "package" | "product";
  items: SaleItem[];
  pricing: Pricing;
  payer: Payer;
  payment: Payment;
  children?: ChildInfo[] | null; // Multi-child support (JSON array from database)
  scheduled_date?: string | null; // Scheduled date for package sales (YYYY-MM-DD format)
  timestamps: SaleTimestamps;
}

export interface SaleItem {
  product_id?: string;
  service_id?: string;
  package_id?: string;
  quantity: number;
  unit_price_cents: number;
  total_price_cents: number;
}

export interface Pricing {
  subtotal_cents: number;
  discount_cents: number;
  total_cents: number;
}

export interface Payer {
  name?: string;
  phone?: string;
  signature?: string | null;  // Base64 encoded signature
}

export interface Payment {
  method: "cash" | "card" | "mixed";
  cash_received_cents?: number;
  card_auth_code?: string;
}

export interface SaleTimestamps {
  created_at: string;
  updated_at?: string;
}

export interface Timer {
  id: string;
  sale_id: string;
  service_id?: string; // Service ID for the timer (used for extending with service slots)
  child_name?: string | null;
  child_age?: number | null;
  start_delay_minutes?: number | null; // Delay before starting timer
  start_at: string;
  end_at: string;
  status: "scheduled" | "active" | "ended" | "extended" | "alert";
  time_left_seconds?: number;
  history: TimerHistory[];
}

export interface TimerHistory {
  event: "start" | "extend" | "end";
  at: string;
  minutes_added?: number;
}

export interface Product {
  id: string;
  sucursal_id: string; // Kept for backward compatibility
  sucursales_ids?: string[]; // New: support for multiple sucursales
  name: string;
  price_cents: number;
  stock_qty: number;
  threshold_alert_qty: number;
  enabled_for_package: boolean;
  package_deduction_qty: number;
  active?: boolean;
}

export interface Service {
  id: string;
  sucursal_id: string; // Kept for backward compatibility
  sucursales_ids?: string[]; // New: support for multiple sucursales
  name: string;
  durations_allowed: number[];
  duration_prices: Record<number, number>; // Required: {duration_minutes: price_cents} for flexible pricing
  alerts_config: ServiceAlert[];
  active?: boolean;
}

export interface ServiceAlert {
  minutes_before: number;
  sound?: string; // Kept for backward compatibility
  sound_enabled?: boolean; // New: enable/disable sound for this alert
  sound_loop?: boolean; // New: loop sound continuously until stopped
}

export interface Package {
  id: string;
  sucursal_id: string; // Kept for backward compatibility
  sucursales_ids?: string[]; // New: support for multiple sucursales
  name: string;
  description: string;
  included_items: PackageItem[];
  price_cents: number;
}

export interface PackageItem {
  product_id?: string;
  service_id?: string;
  quantity?: number; // For products
  duration_minutes?: number; // For services
}

export interface DayStart {
  id: string;
  sucursal_id: string;
  usuario_id: string;
  started_at: string;
  initial_cash_cents: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DayStatus {
  is_open: boolean;
  day_start: DayStart | null;
  current_date: string;
}

export interface DayClose {
  id: string;
  sucursal_id: string;
  usuario_id: string;
  date: string;
  system_total_cents: number;
  physical_count_cents: number;
  difference_cents: number;
  totals: {
    system_total_cents: number;
    system_cash_cents: number;
    sale_count: number;
    physical_count_cents: number;
    difference_cents: number;
  } | null;
  created_at: string;
  updated_at: string;
}

export interface Sucursal {
  id: string;
  identifier: string;  // e.g., "suc01"
  name: string;
  address?: string | null;
  timezone: string;
  active: boolean;
  created_at: string;
  updated_at: string;
}

/** Vista Display: config for alert when timer reaches 0 (sound in Display only). */
export interface ZeroAlertConfig {
  sound_enabled: boolean;
  sound_loop: boolean;
}

/** Display settings per sucursal (Vista Display). */
export interface DisplaySettings {
  zero_alert: ZeroAlertConfig;
}

