/**
 * Package helper functions - Reusable utilities for package operations.
 * 
 * Implements Patrón 3 (Híbrido) + Opción A (Inferido):
 * - Auto-calculate price for products
 * - Manual price for services
 * - Infer package type from included_items
 */

import type { Package, PackageItem, Product } from "@kidyland/shared/types";

/**
 * Infer package type from included_items (Opción A: Inferido).
 * 
 * @param items - Array of PackageItem objects
 * @returns Package type: "product", "service", or "mixed"
 */
export function inferPackageType(
  items: PackageItem[] | null | undefined
): "product" | "service" | "mixed" {
  // Ensure items is an array
  if (!items) {
    return "mixed"; // Default for null/undefined
  }
  
  // Handle case where items might not be an array
  const itemsArray = Array.isArray(items) ? items : [];
  
  if (itemsArray.length === 0) {
    return "mixed"; // Default for empty packages
  }

  const hasProducts = itemsArray.some((item) => item.product_id);
  const hasServices = itemsArray.some((item) => item.service_id);

  if (hasProducts && hasServices) {
    return "mixed";
  }
  if (hasProducts) {
    return "product";
  }
  if (hasServices) {
    return "service";
  }

  return "mixed"; // Fallback
}

/**
 * Calculate automatic price for products in a package (Patrón 3: Híbrido).
 * 
 * Only products contribute to the calculated price.
 * Services are not included in the calculation (they use manual pricing).
 * 
 * Automatically applies package_deduction_qty discounts for products
 * that have enabled_for_package === true.
 * 
 * @param items - Array of items in the package
 * @param products - Array of available products (for price lookup)
 * @returns Calculated price in cents (0 if no products or invalid)
 */
export function calculatePackagePrice(
  items: Array<{
    type: "product" | "service";
    id: string;
    quantity?: number;
  }>,
  products: Product[]
): number {
  return items
    .filter((item) => item.type === "product")
    .reduce((total, item) => {
      const product = products.find((p) => p.id === item.id);
      
      // Skip if product not found or not enabled for packages
      if (!product || !product.enabled_for_package) {
        return total;
      }
      
      // Skip if quantity is invalid
      if (!item.quantity || item.quantity <= 0) {
        return total;
      }
      
      // Apply discount: ensure deduction doesn't exceed price
      const deduction = Math.min(product.package_deduction_qty, product.price_cents);
      const unitPriceAfterDiscount = Math.max(0, product.price_cents - deduction);
      
      return total + unitPriceAfterDiscount * item.quantity;
    }, 0);
}

/**
 * Check if a package price is auto-calculated or manually set.
 * 
 * @param currentPriceCents - Current price in cents
 * @param calculatedPriceCents - Calculated price in cents
 * @param packageType - Type of package ("product", "service", "mixed")
 * @returns true if price matches calculated value (auto), false if manual
 */
export function isPriceAutoCalculated(
  currentPriceCents: number,
  calculatedPriceCents: number,
  packageType: "product" | "service" | "mixed"
): boolean {
  // Services always use manual pricing
  if (packageType === "service") {
    return false;
  }

  // For products/mixed: check if current price matches calculated
  return currentPriceCents === calculatedPriceCents;
}

/**
 * Format package type for display.
 * 
 * @param type - Package type
 * @returns Formatted label
 */
export function formatPackageType(
  type: "product" | "service" | "mixed"
): string {
  const labels: Record<"product" | "service" | "mixed", string> = {
    product: "Productos",
    service: "Servicios",
    mixed: "Mixto",
  };
  return labels[type] || "Mixto";
}




