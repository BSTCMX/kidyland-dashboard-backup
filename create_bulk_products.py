#!/usr/bin/env python3
"""
Script to create bulk products for Kidyland.
Creates all food and beverage products with standardized values.

This script:
- Gets all active sucursales
- Creates 27 products (15 ALIMENTOS + 12 BEBIDAS)
- Assigns all products to all active sucursales
- Uses standardized pricing and stock values
"""
import asyncio
import sys
import os
from pathlib import Path
from typing import List

# Add packages/api to path
api_path = Path(__file__).parent / "packages" / "api"
sys.path.insert(0, str(api_path))

# Change to packages/api directory to load .env file correctly
original_cwd = os.getcwd()
os.chdir(api_path)

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from models.product import Product
from models.sucursal import Sucursal
from core.config import settings
import uuid
import json
import re
import ssl

# Product configuration - standardized values
PRODUCT_CONFIG = {
    "price_cents": 5000,  # 50 pesos
    "stock_qty": 20,
    "threshold_alert_qty": 10,
    "enabled_for_package": True,
    "package_deduction_qty": 1500,  # 15 pesos
    "active": True,
}

# Product names organized by category (for reference only, not stored)
ALIMENTOS = [
    "Palomitas saladas",
    "Palomitas acarameladas",
    "Dorilocos",
    "Nachos",
    "Papas locas",
    "Papas a la francesa",
    "Boneless",
    "Alitas",
    "Hot dogs",
    "Manzanas con chamoy",
    "Manzanas acarameladas",
    "Algodones de azúcar",
    "Salchipulpos",
]

BEBIDAS = [
    "Limonada",
    "Limonada frutos rojos",
    "Naranjada",
    "Squirt preparado",
    "Sangría preparado",
    "Azulitos Kidy",
    "Paletas de agua",
    "Paletas de crema",
    "Sodas italianas",
    "Paletas de hielo",
]

# Combine all products
ALL_PRODUCTS = ALIMENTOS + BEBIDAS


async def get_active_sucursales(db: AsyncSession) -> List[Sucursal]:
    """Get all active sucursales from database."""
    result = await db.execute(
        select(Sucursal).where(Sucursal.active == True)
    )
    return list(result.scalars().all())


async def product_exists(db: AsyncSession, name: str) -> Product | None:
    """Check if a product with the given name already exists (excluding soft-deleted)."""
    result = await db.execute(
        select(Product).where(
            Product.name == name,
            Product.deleted_at.is_(None)  # Only check non-deleted products
        )
    )
    return result.scalar_one_or_none()


async def create_or_update_product(
    db: AsyncSession,
    name: str,
    sucursales_ids: List[str],
    config: dict
) -> tuple[Product, bool]:
    """
    Create a new product or update existing one.
    
    Returns:
        tuple: (Product object, was_created: bool)
    """
    existing = await product_exists(db, name)
    
    if existing:
        # Update existing product
        existing.price_cents = config["price_cents"]
        existing.stock_qty = config["stock_qty"]
        existing.threshold_alert_qty = config["threshold_alert_qty"]
        existing.enabled_for_package = config["enabled_for_package"]
        existing.package_deduction_qty = config["package_deduction_qty"]
        existing.active = config["active"]
        existing.sucursales_ids = sucursales_ids
        # Update sucursal_id from first sucursal for backward compatibility
        if sucursales_ids:
            existing.sucursal_id = uuid.UUID(sucursales_ids[0])
        
        await db.flush()
        await db.refresh(existing)
        return existing, False
    else:
        # Create new product
        if not sucursales_ids:
            raise ValueError(f"Cannot create product '{name}': No sucursales provided")
        
        product = Product(
            id=uuid.uuid4(),
            sucursal_id=uuid.UUID(sucursales_ids[0]),  # First sucursal for backward compatibility
            sucursales_ids=sucursales_ids,  # All sucursales
            name=name,
            price_cents=config["price_cents"],
            stock_qty=config["stock_qty"],
            threshold_alert_qty=config["threshold_alert_qty"],
            enabled_for_package=config["enabled_for_package"],
            package_deduction_qty=config["package_deduction_qty"],
            active=config["active"],
        )
        db.add(product)
        await db.flush()
        await db.refresh(product)
        return product, True


async def create_bulk_products():
    """Main function to create all products."""
    # Get database URL from settings and convert to async format
    database_url = settings.DATABASE_URL
    
    # Convert to async format (postgresql:// -> postgresql+asyncpg://)
    async_database_url = database_url
    if async_database_url.startswith("postgresql://"):
        async_database_url = async_database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif async_database_url.startswith("postgres://"):
        async_database_url = async_database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    # Check if SSL is required
    ssl_required = "sslmode=require" in database_url.lower()
    
    # Remove sslmode and channel_binding from URL (asyncpg doesn't accept them as URL params)
    async_database_url = re.sub(r'[?&]sslmode=[^&]*', '', async_database_url)
    async_database_url = re.sub(r'[?&]channel_binding=[^&]*', '', async_database_url)
    async_database_url = re.sub(r'[?&]+$', '', async_database_url)
    
    # Configure SSL if required
    connect_args = {}
    if ssl_required:
        ssl_context = ssl.create_default_context()
        if os.getenv("ENVIRONMENT", "development") == "development":
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ssl_context
    
    # Create async engine
    engine = create_async_engine(
        async_database_url,
        pool_pre_ping=True,
        echo=False,
        connect_args=connect_args if connect_args else {}
    )
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Get all active sucursales
        sucursales = await get_active_sucursales(db)
        
        if not sucursales:
            print("❌ Error: No active sucursales found. Please create a sucursal first.")
            return
        
        print(f"✅ Found {len(sucursales)} active sucursale(s):")
        for sucursal in sucursales:
            print(f"   - {sucursal.name} (ID: {sucursal.id})")
        
        # Get sucursal IDs as strings for sucursales_ids
        sucursal_ids = [str(s.id) for s in sucursales]
        
        print(f"\n📦 Creating {len(ALL_PRODUCTS)} products...")
        print(f"   Configuration:")
        print(f"   - Price: ${PRODUCT_CONFIG['price_cents'] / 100:.2f}")
        print(f"   - Stock: {PRODUCT_CONFIG['stock_qty']}")
        print(f"   - Alert Threshold: {PRODUCT_CONFIG['threshold_alert_qty']}")
        print(f"   - Package Enabled: {PRODUCT_CONFIG['enabled_for_package']}")
        print(f"   - Package Discount: ${PRODUCT_CONFIG['package_deduction_qty'] / 100:.2f}")
        print(f"   - Active: {PRODUCT_CONFIG['active']}")
        print(f"   - Sucursales: {len(sucursal_ids)}")
        
        # Track results
        created_count = 0
        updated_count = 0
        errors = []
        
        # Create/update each product
        for i, product_name in enumerate(ALL_PRODUCTS, 1):
            try:
                product, was_created = await create_or_update_product(
                    db=db,
                    name=product_name,
                    sucursales_ids=sucursal_ids,
                    config=PRODUCT_CONFIG
                )
                
                if was_created:
                    created_count += 1
                    status = "✅ Created"
                else:
                    updated_count += 1
                    status = "🔄 Updated"
                
                print(f"   [{i:2d}/{len(ALL_PRODUCTS)}] {status}: {product_name}")
                
            except Exception as e:
                error_msg = f"❌ Error creating '{product_name}': {str(e)}"
                errors.append(error_msg)
                print(f"   [{i:2d}/{len(ALL_PRODUCTS)}] {error_msg}")
        
        # Commit all changes
        try:
            await db.commit()
            print(f"\n✅ Transaction committed successfully!")
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error committing transaction: {str(e)}")
            return
        
        # Print summary
        print(f"\n📊 Summary:")
        print(f"   - Total products processed: {len(ALL_PRODUCTS)}")
        print(f"   - Created: {created_count}")
        print(f"   - Updated: {updated_count}")
        print(f"   - Errors: {len(errors)}")
        
        if errors:
            print(f"\n⚠️  Errors encountered:")
            for error in errors:
                print(f"   {error}")
        else:
            print(f"\n🎉 All products created/updated successfully!")
    
    await engine.dispose()
    # Restore original working directory
    os.chdir(original_cwd)


if __name__ == "__main__":
    asyncio.run(create_bulk_products())

