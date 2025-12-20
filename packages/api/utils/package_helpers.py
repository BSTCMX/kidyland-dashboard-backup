"""
Package helper utilities for report and analytics.

Reusable functions for package type identification and filtering.
"""

from typing import List, Dict, Any
from models.package import Package


def is_service_package(package: Package) -> bool:
    """
    Check if a package contains only services (no products).
    
    A service package must:
    - Have at least one item
    - All items must have service_id (not None)
    - No items should have product_id (all should be None)
    
    Args:
        package: Package model instance
        
    Returns:
        True if package contains only services, False otherwise
    """
    items = package.included_items or []
    
    # Empty packages are not service packages
    if not items:
        return False
    
    # Check that all items are services
    has_products = any(item.get("product_id") is not None for item in items)
    has_services = any(item.get("service_id") is not None for item in items)
    
    # Service package: has services AND no products
    return has_services and not has_products


def filter_service_packages(packages: List[Package]) -> List[Package]:
    """
    Filter a list of packages to return only service packages.
    
    Args:
        packages: List of Package instances
        
    Returns:
        List of packages that contain only services
    """
    return [pkg for pkg in packages if is_service_package(pkg)]


def get_service_package_ids(packages: List[Package]) -> List[Any]:
    """
    Extract IDs from service packages.
    
    Useful for filtering sales by service package IDs.
    
    Args:
        packages: List of Package instances
        
    Returns:
        List of package IDs (UUIDs) that are service packages
    """
    service_packages = filter_service_packages(packages)
    return [pkg.id for pkg in service_packages]


def is_product_package(package: Package) -> bool:
    """
    Check if a package contains only products (no services).
    
    A product package must:
    - Have at least one item
    - All items must have product_id (not None)
    - No items should have service_id (all should be None)
    
    Args:
        package: Package model instance
        
    Returns:
        True if package contains only products, False otherwise
    """
    items = package.included_items or []
    
    # Empty packages are not product packages
    if not items:
        return False
    
    # Check that all items are products
    has_products = any(item.get("product_id") is not None for item in items)
    has_services = any(item.get("service_id") is not None for item in items)
    
    # Product package: has products AND no services
    return has_products and not has_services


def filter_product_packages(packages: List[Package]) -> List[Package]:
    """
    Filter a list of packages to return only product packages.
    
    Args:
        packages: List of Package instances
        
    Returns:
        List of packages that contain only products
    """
    return [pkg for pkg in packages if is_product_package(pkg)]


def get_product_package_ids(packages: List[Package]) -> List[Any]:
    """
    Extract IDs from product packages.
    
    Useful for filtering sales by product package IDs.
    
    Args:
        packages: List of Package instances
        
    Returns:
        List of package IDs (UUIDs) that are product packages
    """
    product_packages = filter_product_packages(packages)
    return [pkg.id for pkg in product_packages]






