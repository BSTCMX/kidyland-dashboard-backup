#!/usr/bin/env python3
"""
Script to create a test product with specific data.
This script creates a product called "palomitas" with the specified values.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add packages/api to path
api_path = Path(__file__).parent / "packages" / "api"
sys.path.insert(0, str(api_path))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from models.product import Product
from models.sucursal import Sucursal
from database import get_db_url
import uuid

async def create_palomitas_product():
    """Create the palomitas product with specified values."""
    # Get database URL
    db_url = get_db_url()
    engine = create_async_engine(db_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Get first active sucursal
        result = await db.execute(select(Sucursal).where(Sucursal.active == True).limit(1))
        sucursal = result.scalar_one_or_none()
        
        if not sucursal:
            print("❌ Error: No active sucursal found. Please create a sucursal first.")
            return
        
        print(f"✅ Using sucursal: {sucursal.name} (ID: {sucursal.id})")
        
        # Check if product already exists
        existing = await db.execute(
            select(Product).where(
                Product.name.ilike("palomitas"),
                Product.sucursal_id == sucursal.id
            )
        )
        existing_product = existing.scalar_one_or_none()
        
        if existing_product:
            print(f"⚠️  Product 'palomitas' already exists. Updating it...")
            # Update existing product
            existing_product.price_cents = 5000  # 50 pesos = 5000 centavos
            existing_product.stock_qty = 20
            existing_product.threshold_alert_qty = 10
            existing_product.enabled_for_package = True
            existing_product.package_deduction_qty = 1500  # 15 pesos = 1500 centavos
            existing_product.active = True
            await db.commit()
            await db.refresh(existing_product)
            print(f"✅ Product updated successfully!")
            print(f"   ID: {existing_product.id}")
            print(f"   Name: {existing_product.name}")
            print(f"   Price: ${existing_product.price_cents / 100:.2f}")
            print(f"   Stock: {existing_product.stock_qty}")
            print(f"   Threshold: {existing_product.threshold_alert_qty}")
            print(f"   Package enabled: {existing_product.enabled_for_package}")
            print(f"   Package deduction: ${existing_product.package_deduction_qty / 100:.2f}")
        else:
            # Create new product
            product = Product(
                id=uuid.uuid4(),
                sucursal_id=sucursal.id,
                name="palomitas",
                price_cents=5000,  # 50 pesos = 5000 centavos
                stock_qty=20,
                threshold_alert_qty=10,
                enabled_for_package=True,
                package_deduction_qty=1500,  # 15 pesos = 1500 centavos
                active=True
            )
            db.add(product)
            await db.commit()
            await db.refresh(product)
            print(f"✅ Product created successfully!")
            print(f"   ID: {product.id}")
            print(f"   Name: {product.name}")
            print(f"   Price: ${product.price_cents / 100:.2f}")
            print(f"   Stock: {product.stock_qty}")
            print(f"   Threshold: {product.threshold_alert_qty}")
            print(f"   Package enabled: {product.enabled_for_package}")
            print(f"   Package deduction: ${product.package_deduction_qty / 100:.2f}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_palomitas_product())

