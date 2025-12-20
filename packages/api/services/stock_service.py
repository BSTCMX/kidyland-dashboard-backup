"""
Stock service - Business logic for stock management.
"""
import logging
import uuid
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from sqlalchemy.orm import selectinload
from uuid import UUID
from models.product import Product
from models.package import Package
from services.analytics_cache import get_cache

logger = logging.getLogger(__name__)


class StockService:
    """Service for handling stock operations."""
    
    @staticmethod
    async def get_stock_alerts(
        db: AsyncSession,
        sucursal_id: str
    ) -> List[Product]:
        """
        Get products with stock at or below threshold.
        
        Args:
            db: Database session
            sucursal_id: Sucursal ID to filter by (string, will be converted to UUID)
            
        Returns:
            List of Product objects with stock alerts, ordered by stock ASC
        """
        # Convert string to UUID
        try:
            sucursal_uuid = uuid.UUID(sucursal_id)
        except ValueError:
            logger.error(f"Invalid sucursal_id format: {sucursal_id}")
            return []
        
        result = await db.execute(
            select(Product).where(
                and_(
                    Product.sucursal_id == sucursal_uuid,
                    Product.active == True,
                    Product.stock_qty <= Product.threshold_alert_qty
                )
            ).order_by(Product.stock_qty.asc())
        )
        products = result.scalars().all()
        
        logger.info(
            f"Found {len(products)} products with stock alerts "
            f"for sucursal {sucursal_id}"
        )
        return list(products)
    
    @staticmethod
    async def validate_stock_availability(
        db: AsyncSession,
        items: List[Dict[str, Any]],
        sucursal_id: UUID
    ) -> Tuple[bool, List[str]]:
        """
        Validate that all products in sale items have sufficient stock.
        
        This method handles:
        - Direct product sales (type="product")
        - Package sales (type="package") - decomposes package and validates each product
        
        Args:
            db: Database session
            items: List of sale items with structure:
                - type: "product" or "package"
                - ref_id: UUID of product or package
                - quantity: quantity to sell
            sucursal_id: Sucursal UUID to filter products
            
        Returns:
            Tuple of (is_valid: bool, errors: List[str])
            - is_valid: True if all products have sufficient stock
            - errors: List of error messages for products with insufficient stock
            
        Raises:
            ValueError: If product or package not found
        """
        errors = []
        product_requirements: Dict[UUID, int] = {}  # product_id -> total_quantity_needed
        
        # Process each sale item
        for item in items:
            item_type = item.get("type")
            ref_id_str = item.get("ref_id")
            quantity = item.get("quantity", 1)
            
            if not ref_id_str:
                errors.append(f"Item missing ref_id: {item}")
                continue
            
            try:
                ref_id = UUID(ref_id_str) if isinstance(ref_id_str, str) else ref_id_str
            except (ValueError, TypeError):
                errors.append(f"Invalid ref_id format: {ref_id_str}")
                continue
            
            if item_type == "product":
                # Direct product sale: validate product stock
                product_result = await db.execute(
                    select(Product).where(
                        and_(
                            Product.id == ref_id,
                            Product.sucursal_id == sucursal_id,
                            Product.active == True
                        )
                    )
                )
                product = product_result.scalar_one_or_none()
                
                if not product:
                    errors.append(f"Product with ID {ref_id} not found or inactive")
                    continue
                
                # Accumulate quantity needed for this product
                current_need = product_requirements.get(ref_id, 0)
                product_requirements[ref_id] = current_need + quantity
                
            elif item_type == "package":
                # Package sale: decompose package and validate each product
                package_result = await db.execute(
                    select(Package).where(
                        and_(
                            Package.id == ref_id,
                            Package.sucursal_id == sucursal_id,
                            Package.active == True
                        )
                    )
                )
                package = package_result.scalar_one_or_none()
                
                if not package:
                    errors.append(f"Package with ID {ref_id} not found or inactive")
                    continue
                
                # Decompose package: get included_items
                included_items = package.included_items or []
                
                # Process each item in the package
                for package_item in included_items:
                    product_id_str = package_item.get("product_id")
                    
                    # Skip if this package item is a service (not a product)
                    if not product_id_str:
                        continue
                    
                    try:
                        product_id = UUID(product_id_str) if isinstance(product_id_str, str) else product_id_str
                    except (ValueError, TypeError):
                        errors.append(f"Invalid product_id in package item: {product_id_str}")
                        continue
                    
                    # Get quantity from package item (required for products)
                    item_quantity = package_item.get("quantity")
                    if item_quantity is None or item_quantity <= 0:
                        errors.append(f"Package item missing or invalid quantity for product {product_id}")
                        continue
                    
                    # Total quantity needed = package_item.quantity * sale.quantity
                    total_quantity_needed = item_quantity * quantity
                    
                    # Accumulate quantity needed for this product
                    current_need = product_requirements.get(product_id, 0)
                    product_requirements[product_id] = current_need + total_quantity_needed
            else:
                # Service sales don't require stock validation
                continue
        
        # If we have errors from processing items, return early
        if errors:
            return False, errors
        
        # Validate stock for all products
        for product_id, required_quantity in product_requirements.items():
            product_result = await db.execute(
                select(Product).where(
                    and_(
                        Product.id == product_id,
                        Product.sucursal_id == sucursal_id,
                        Product.active == True
                    )
                )
            )
            product = product_result.scalar_one_or_none()
            
            if not product:
                errors.append(f"Product with ID {product_id} not found or inactive")
                continue
            
            if product.stock_qty < required_quantity:
                errors.append(
                    f"Product '{product.name}' (ID: {product_id}) has insufficient stock. "
                    f"Required: {required_quantity}, Available: {product.stock_qty}"
                )
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    @staticmethod
    async def decrement_stock_atomic(
        db: AsyncSession,
        items: List[Dict[str, Any]],
        sucursal_id: UUID
    ) -> None:
        """
        Decrement stock for all products in sale items atomically.
        
        This method handles:
        - Direct product sales (type="product")
        - Package sales (type="package") - decomposes package and decrements each product
        
        Uses atomic UPDATE with WHERE clause to ensure stock doesn't go negative
        and prevents race conditions.
        
        Args:
            db: Database session
            items: List of sale items with structure:
                - type: "product" or "package"
                - ref_id: UUID of product or package
                - quantity: quantity to sell
            sucursal_id: Sucursal UUID to filter products
            
        Raises:
            ValueError: If product or package not found, or insufficient stock
        """
        product_decrements: Dict[UUID, int] = {}  # product_id -> total_quantity_to_decrement
        
        # Process each sale item to calculate total decrements needed
        for item in items:
            item_type = item.get("type")
            ref_id_str = item.get("ref_id")
            quantity = item.get("quantity", 1)
            
            if not ref_id_str:
                raise ValueError(f"Item missing ref_id: {item}")
            
            try:
                ref_id = UUID(ref_id_str) if isinstance(ref_id_str, str) else ref_id_str
            except (ValueError, TypeError):
                raise ValueError(f"Invalid ref_id format: {ref_id_str}")
            
            if item_type == "product":
                # Direct product sale: decrement product stock
                current_decrement = product_decrements.get(ref_id, 0)
                product_decrements[ref_id] = current_decrement + quantity
                
            elif item_type == "package":
                # Package sale: decompose package and decrement each product
                package_result = await db.execute(
                    select(Package).where(
                        and_(
                            Package.id == ref_id,
                            Package.sucursal_id == sucursal_id,
                            Package.active == True
                        )
                    )
                )
                package = package_result.scalar_one_or_none()
                
                if not package:
                    raise ValueError(f"Package with ID {ref_id} not found or inactive")
                
                # Decompose package: get included_items
                included_items = package.included_items or []
                
                # Process each item in the package
                for package_item in included_items:
                    product_id_str = package_item.get("product_id")
                    
                    # Skip if this package item is a service (not a product)
                    if not product_id_str:
                        continue
                    
                    try:
                        product_id = UUID(product_id_str) if isinstance(product_id_str, str) else product_id_str
                    except (ValueError, TypeError):
                        raise ValueError(f"Invalid product_id in package item: {product_id_str}")
                    
                    # Get quantity from package item (required for products)
                    item_quantity = package_item.get("quantity")
                    if item_quantity is None or item_quantity <= 0:
                        raise ValueError(f"Package item missing or invalid quantity for product {product_id}")
                    
                    # Total quantity to decrement = package_item.quantity * sale.quantity
                    total_quantity_to_decrement = item_quantity * quantity
                    
                    # Accumulate decrement for this product
                    current_decrement = product_decrements.get(product_id, 0)
                    product_decrements[product_id] = current_decrement + total_quantity_to_decrement
            else:
                # Service sales don't require stock decrement
                continue
        
        # Track products that were updated (for cache invalidation)
        products_updated: List[UUID] = []
        
        # Perform atomic decrements for all products
        for product_id, quantity_to_decrement in product_decrements.items():
            # Atomic UPDATE: only decrement if stock >= quantity_to_decrement
            # This prevents negative stock and handles race conditions
            result = await db.execute(
                update(Product)
                .where(
                    and_(
                        Product.id == product_id,
                        Product.sucursal_id == sucursal_id,
                        Product.active == True,
                        Product.stock_qty >= quantity_to_decrement
                    )
                )
                .values(stock_qty=Product.stock_qty - quantity_to_decrement)
            )
            
            # Check if any rows were updated
            if result.rowcount == 0:
                # Get product name for error message
                product_result = await db.execute(
                    select(Product).where(Product.id == product_id)
                )
                product = product_result.scalar_one_or_none()
                product_name = product.name if product else f"ID {product_id}"
                
                raise ValueError(
                    f"Failed to decrement stock for product '{product_name}' (ID: {product_id}). "
                    f"Insufficient stock or product not found/inactive. "
                    f"Required: {quantity_to_decrement}"
                )
            
            # Track this product for potential cache invalidation
            products_updated.append(product_id)
            
            logger.info(
                f"Decremented stock for product {product_id}: "
                f"-{quantity_to_decrement} units"
            )
        
        # Flush to ensure changes are persisted (but don't commit yet - let caller handle transaction)
        await db.flush()
        
        # Invalidate stock cache after successful stock decrement
        # This ensures fresh data on next report request
        try:
            cache = get_cache()
            # Invalidate cache for this specific sucursal
            sucursal_id_str = str(sucursal_id)
            await cache.invalidate(f"stock:{sucursal_id_str}")
            # Also invalidate global stock cache (for "all sucursales" queries)
            await cache.invalidate("stock:*")
            logger.debug(
                f"Invalidated stock cache for sucursal {sucursal_id_str} "
                f"after decrementing {len(products_updated)} products"
            )
        except Exception as e:
            # Log error but don't fail the transaction
            # Cache invalidation is a performance optimization, not critical
            logger.warning(
                f"Failed to invalidate stock cache after decrement: {e}. "
                f"This is non-critical and won't affect the sale."
            )




