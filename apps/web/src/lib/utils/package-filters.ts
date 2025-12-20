/**
 * Package filter utilities - Filter packages by type.
 * 
 * Reusable utilities for filtering packages based on their type
 * (service, product, or mixed).
 */

import type { Package } from "@kidyland/shared/types";
import { inferPackageType } from "./package-helpers";

/**
 * Filter packages to show only service packages.
 * 
 * A service package is one that contains only services (no products).
 * 
 * @param packages - Array of all packages
 * @returns Array of packages that contain only services
 */
export function filterServicePackages(packages: Package[]): Package[] {
  return packages.filter((pkg) => {
    const type = inferPackageType(pkg.included_items);
    return type === "service";
  });
}

/**
 * Filter packages to show only product packages.
 * 
 * A product package is one that contains only products (no services).
 * 
 * @param packages - Array of all packages
 * @returns Array of packages that contain only products
 */
export function filterProductPackages(packages: Package[]): Package[] {
  return packages.filter((pkg) => {
    const type = inferPackageType(pkg.included_items);
    return type === "product";
  });
}

/**
 * Filter packages to show only active packages.
 * 
 * @param packages - Array of all packages
 * @returns Array of packages that are active
 */
export function filterActivePackages(packages: Package[]): Package[] {
  return packages.filter((pkg) => pkg.active !== false);
}

/**
 * Filter packages to show active service packages only.
 * 
 * Convenience function that combines both filters.
 * 
 * @param packages - Array of all packages
 * @returns Array of active packages that contain only services
 */
export function filterActiveServicePackages(packages: Package[]): Package[] {
  return filterServicePackages(filterActivePackages(packages));
}

/**
 * Filter packages to show active product packages only.
 * 
 * Convenience function that combines both filters.
 * 
 * @param packages - Array of all packages
 * @returns Array of active packages that contain only products
 */
export function filterActiveProductPackages(packages: Package[]): Package[] {
  return filterProductPackages(filterActivePackages(packages));
}










