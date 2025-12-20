/**
 * Package Grouping Utilities - Logic for grouping items with related packages.
 * 
 * Implements intelligent grouping options:
 * - All items together
 * - Services with related packages
 * - Products with related packages
 */

import type { ServiceItem, ProductItem, PackageItem } from "$lib/utils/video-canvas";
import type { Package } from "@kidyland/shared/types";

export type GroupingMode = "all" | "services-with-packages" | "products-with-packages";

export interface GroupedItems {
  services: ServiceItem[];
  products: ProductItem[];
  packages: PackageItem[];
}

/**
 * Get packages that contain a specific service ID.
 */
function getPackagesForService(
  serviceId: string,
  allPackages: Package[]
): PackageItem[] {
  return allPackages
    .filter((pkg) =>
      pkg.included_items?.some((item) => item.service_id === serviceId)
    )
    .map((pkg) => ({
      id: pkg.id,
      name: pkg.name,
      price_cents: pkg.price_cents,
      description: pkg.description || undefined,
    }));
}

/**
 * Get packages that contain a specific product ID.
 */
function getPackagesForProduct(
  productId: string,
  allPackages: Package[]
): PackageItem[] {
  return allPackages
    .filter((pkg) =>
      pkg.included_items?.some((item) => item.product_id === productId)
    )
    .map((pkg) => ({
      id: pkg.id,
      name: pkg.name,
      price_cents: pkg.price_cents,
      description: pkg.description || undefined,
    }));
}

/**
 * Group items based on the selected grouping mode.
 * 
 * @param services - Array of selected services
 * @param products - Array of selected products
 * @param allPackages - Array of all available packages (from store)
 * @param mode - Grouping mode
 * @returns Grouped items according to the mode
 */
export function groupItems(
  services: ServiceItem[],
  products: ProductItem[],
  allPackages: Package[],
  mode: GroupingMode
): GroupedItems {
  switch (mode) {
    case "all": {
      // Return all items together, including all packages
      const packages: PackageItem[] = allPackages.map((pkg) => ({
        id: pkg.id,
        name: pkg.name,
        price_cents: pkg.price_cents,
        description: pkg.description || undefined,
      }));

      return {
        services,
        products,
        packages,
      };
    }

    case "services-with-packages": {
      // Group services with their related packages only
      const relatedPackagesMap = new Map<string, PackageItem>();

      services.forEach((service) => {
        const relatedPackages = getPackagesForService(service.id, allPackages);
        relatedPackages.forEach((pkg) => {
          // Use Map to avoid duplicates
          if (!relatedPackagesMap.has(pkg.id)) {
            relatedPackagesMap.set(pkg.id, pkg);
          }
        });
      });

      return {
        services,
        products: [], // Products not included in this mode
        packages: Array.from(relatedPackagesMap.values()),
      };
    }

    case "products-with-packages": {
      // Group products with their related packages only
      const relatedPackagesMap = new Map<string, PackageItem>();

      products.forEach((product) => {
        const relatedPackages = getPackagesForProduct(product.id, allPackages);
        relatedPackages.forEach((pkg) => {
          // Use Map to avoid duplicates
          if (!relatedPackagesMap.has(pkg.id)) {
            relatedPackagesMap.set(pkg.id, pkg);
          }
        });
      });

      return {
        services: [], // Services not included in this mode
        products,
        packages: Array.from(relatedPackagesMap.values()),
      };
    }

    default:
      // Fallback to "all"
      return {
        services,
        products,
        packages: allPackages.map((pkg) => ({
          id: pkg.id,
          name: pkg.name,
          price_cents: pkg.price_cents,
          description: pkg.description || undefined,
        })),
      };
  }
}

/**
 * Get grouping mode label for display.
 */
export function getGroupingModeLabel(mode: GroupingMode): string {
  const labels: Record<GroupingMode, string> = {
    all: "Todos los items juntos",
    "services-with-packages": "Servicios + Paquetes relacionados",
    "products-with-packages": "Productos + Paquetes relacionados",
  };
  return labels[mode] || labels.all;
}
