"""
Catalog endpoints for sucursales, services, and products.

Security Rules:
- GET endpoints: super_admin and admin_viewer can view
- POST endpoints: Only super_admin can create
"""
import uuid
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, text, and_
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.exc import IntegrityError
from typing import List
import logging
from database import get_db
from schemas.sucursal import (
    SucursalCreate,
    SucursalRead,
    SucursalUpdate,
    DisplaySettingsRead,
    DisplaySettingsUpdate,
    ZeroAlertConfig,
)
from schemas.product import ProductCreate, ProductRead, ProductUpdate
from schemas.service import ServiceCreate, ServiceRead, ServiceUpdate
from schemas.package import PackageCreate, PackageRead, PackageUpdate
from models.sucursal import Sucursal
from models.product import Product
from models.service import Service
from models.package import Package
from utils.auth import require_role, get_current_user
from models.user import User
from utils.update_helpers import apply_intelligent_update

router = APIRouter(prefix="", tags=["catalog"])
logger = logging.getLogger(__name__)


# ========== SUCURSALES ==========

# IMPORTANT: Route order matters in FastAPI - specific routes must come before general ones
# More specific paths (e.g. .../display-settings) must come before /sucursales/{sucursal_id}


def _display_settings_from_sucursal(sucursal: Sucursal) -> DisplaySettingsRead:
    """Build DisplaySettingsRead from sucursal.display_settings JSON or defaults."""
    raw = sucursal.display_settings or {}
    za = raw.get("zero_alert") or {}
    return DisplaySettingsRead(
        zero_alert=ZeroAlertConfig(
            sound_enabled=za.get("sound_enabled", False),
            sound_loop=za.get("sound_loop", False),
        )
    )


@router.get(
    "/sucursales/{sucursal_id}/display-settings/public",
    response_model=DisplaySettingsRead,
)
async def get_display_settings_public(
    sucursal_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Public read-only display settings for Vista Display (kiosk/TV).
    No auth required. Returns only zero_alert (sound_enabled, sound_loop).
    """
    try:
        sucursal_uuid = uuid.UUID(sucursal_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sucursal_id format: {sucursal_id}",
        )
    result = await db.execute(select(Sucursal).where(Sucursal.id == sucursal_uuid))
    sucursal = result.scalar_one_or_none()
    if not sucursal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sucursal not found",
        )
    settings = _display_settings_from_sucursal(sucursal)
    logger.info(
        "[Display] GET display-settings/public sucursal_id=%s sound_enabled=%s",
        sucursal_id,
        settings.zero_alert.sound_enabled,
    )
    return settings


@router.get(
    "/sucursales/{sucursal_id}/display-settings",
    response_model=DisplaySettingsRead,
    dependencies=[Depends(require_role(["super_admin", "recepcion"]))],
)
async def get_display_settings(
    sucursal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get display settings for a sucursal (Vista Display: zero_alert etc.).
    Used by Vista Display to read config. Reception and super_admin can read.
    """
    try:
        sucursal_uuid = uuid.UUID(sucursal_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sucursal_id format: {sucursal_id}",
        )
    result = await db.execute(select(Sucursal).where(Sucursal.id == sucursal_uuid))
    sucursal = result.scalar_one_or_none()
    if not sucursal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sucursal not found",
        )
    if current_user.sucursal_id and sucursal.id != current_user.sucursal_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sucursal not found",
        )
    return _display_settings_from_sucursal(sucursal)


@router.put(
    "/sucursales/{sucursal_id}/display-settings",
    response_model=DisplaySettingsRead,
    dependencies=[Depends(require_role(["super_admin", "recepcion"]))],
)
async def update_display_settings(
    sucursal_id: str,
    payload: DisplaySettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update display settings for a sucursal. Configured from Ventana Timers (Recepción).
    """
    try:
        sucursal_uuid = uuid.UUID(sucursal_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sucursal_id format: {sucursal_id}",
        )
    result = await db.execute(select(Sucursal).where(Sucursal.id == sucursal_uuid))
    sucursal = result.scalar_one_or_none()
    if not sucursal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sucursal not found",
        )
    if current_user.sucursal_id and sucursal.id != current_user.sucursal_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sucursal not found",
        )
    raw = (sucursal.display_settings or {}).copy()
    if payload.zero_alert is not None:
        raw["zero_alert"] = payload.zero_alert.model_dump()
    sucursal.display_settings = raw
    await db.commit()
    await db.refresh(sucursal)
    return _display_settings_from_sucursal(sucursal)


@router.get("/sucursales/{sucursal_id}", response_model=SucursalRead)
async def get_sucursal(
    sucursal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific sucursal by ID.
    
    Security: All authenticated users can view their own sucursal.
    Users with sucursal_id can only view their own sucursal.
    super_admin and admin_viewer can view any sucursal.
    
    Returns:
        Sucursal object
    """
    try:
        sucursal_uuid = uuid.UUID(sucursal_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sucursal_id format: {sucursal_id}"
        )
    
    result = await db.execute(select(Sucursal).where(Sucursal.id == sucursal_uuid))
    sucursal = result.scalar_one_or_none()
    
    if not sucursal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sucursal with ID {sucursal_id} not found"
        )
    
    # Check if user has access to this sucursal
    # If user has sucursal_id, they can only see their own sucursal
    if current_user.sucursal_id and sucursal.id != current_user.sucursal_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sucursal with ID {sucursal_id} not found"
        )
    # super_admin and admin_viewer (users without sucursal_id) can view any sucursal
    
    return sucursal


@router.get("/sucursales", response_model=List[SucursalRead], dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_sucursales(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all sucursales.
    
    Security: super_admin and admin_viewer can view.
    """
    result = await db.execute(select(Sucursal))
    sucursales = result.scalars().all()
    return list(sucursales)


@router.post("/sucursales", response_model=SucursalRead, dependencies=[Depends(require_role("super_admin"))])
async def create_sucursal(
    sucursal_data: SucursalCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new sucursal.
    
    Security: Only super_admin can create.
    """
    # Validate identifier format (alphanumeric, max 20 chars)
    if not sucursal_data.identifier or not sucursal_data.identifier.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identifier is required"
        )
    
    identifier = sucursal_data.identifier.strip()
    if len(identifier) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identifier cannot exceed 20 characters"
        )
    
    if not identifier.replace("_", "").replace("-", "").isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identifier can only contain letters, numbers, underscores, and hyphens"
        )
    
    # Check if identifier already exists
    existing = await db.execute(
        select(Sucursal).where(Sucursal.identifier == identifier)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Identifier '{identifier}' already exists"
        )
    
    sucursal = Sucursal(**sucursal_data.model_dump())
    db.add(sucursal)
    await db.commit()
    await db.refresh(sucursal)
    return sucursal


@router.put("/sucursales/{sucursal_id}", response_model=SucursalRead, dependencies=[Depends(require_role("super_admin"))])
async def update_sucursal(
    sucursal_id: str,
    sucursal_data: SucursalUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing sucursal.
    
    Security: Only super_admin can update.
    """
    try:
        sucursal_uuid = uuid.UUID(sucursal_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sucursal ID format"
        )
    
    result = await db.execute(select(Sucursal).where(Sucursal.id == sucursal_uuid))
    sucursal = result.scalar_one_or_none()
    
    if not sucursal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sucursal not found"
        )
    
    # Validate identifier if provided
    if sucursal_data.identifier is not None:
        identifier = sucursal_data.identifier.strip()
        if not identifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Identifier cannot be empty"
            )
        
        if len(identifier) > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Identifier cannot exceed 20 characters"
            )
        
        if not identifier.replace("_", "").replace("-", "").isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Identifier can only contain letters, numbers, underscores, and hyphens"
            )
        
        # Check if identifier already exists (excluding current sucursal)
        existing = await db.execute(
            select(Sucursal).where(
                Sucursal.identifier == identifier,
                Sucursal.id != sucursal_uuid
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Identifier '{identifier}' already exists"
            )
    
    # Update fields
    update_data = sucursal_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sucursal, field, value)
    
    await db.commit()
    await db.refresh(sucursal)
    return sucursal


@router.delete("/sucursales/{sucursal_id}", dependencies=[Depends(require_role("super_admin"))])
async def delete_sucursal(
    sucursal_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete (soft delete) a sucursal by setting active=False.
    
    Security: Only super_admin can delete.
    """
    try:
        sucursal_uuid = uuid.UUID(sucursal_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sucursal ID format"
        )
    
    result = await db.execute(select(Sucursal).where(Sucursal.id == sucursal_uuid))
    sucursal = result.scalar_one_or_none()
    
    if not sucursal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sucursal not found"
        )
    
    # Soft delete: set active=False
    sucursal.active = False
    await db.commit()
    
    return {"message": "Sucursal deleted successfully"}


# ========== PRODUCTS ==========

@router.get("/products", response_model=List[ProductRead], dependencies=[Depends(require_role(["super_admin", "admin_viewer", "kidibar", "recepcion"]))])
async def get_products(
    sucursal_id: str = Query(None, description="Optional: Filter by sucursal ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get products.
    If sucursal_id is provided, filter by sucursal.
    
    Filtering logic:
    - Only returns products that are not soft-deleted (deleted_at IS NULL)
    - Products where sucursal_id matches (backward compatibility)
    - OR products where sucursales_ids JSON array contains the sucursal_id
    
    Security: super_admin, admin_viewer, kidibar, and recepcion can view.
    """
    query = select(Product).where(Product.deleted_at.is_(None))  # Exclude soft-deleted products
    if sucursal_id:
        try:
            sucursal_uuid = uuid.UUID(sucursal_id)
            sucursal_id_str = str(sucursal_uuid)
            
            # Hybrid filtering: sucursal_id OR sucursales_ids contains
            # Using PostgreSQL JSON functions compatible with JSON (not JSONB)
            # We need to handle NULL and empty arrays safely
            sucursal_id_condition = text(
                """
                EXISTS (
                    SELECT 1 
                    FROM json_array_elements_text(
                        COALESCE(products.sucursales_ids::text::json, '[]'::json)
                    ) AS elem 
                    WHERE trim(both '"' from elem::text) = :sucursal_id_str
                )
                """
            ).bindparams(sucursal_id_str=sucursal_id_str)
            
            query = query.where(
                or_(
                    # Primary sucursal_id match (backward compatibility)
                    Product.sucursal_id == sucursal_uuid,
                    # Check if sucursales_ids array contains the sucursal_id
                    # Only check if sucursales_ids is not NULL and not empty
                    and_(
                        Product.sucursales_ids.isnot(None),
                        # Check that array is not empty using json_array_length
                        text("json_array_length(COALESCE(products.sucursales_ids::text::json, '[]'::json)) > 0"),
                        sucursal_id_condition
                    )
                )
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid sucursal ID format"
            )
    result = await db.execute(query)
    products = result.scalars().all()
    products_list = list(products)
    
    # Logging for debugging (only in development/debug mode)
    if sucursal_id:
        logger.info(f"Found {len(products_list)} products for sucursal_id={sucursal_id}")
        if len(products_list) == 0:
            logger.warning(f"No products found for sucursal_id={sucursal_id} - this might indicate a filtering issue")
        elif logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Products found: {[p.name for p in products_list[:5]]}")  # Log first 5 names
    
    return products_list


@router.post("/products", response_model=ProductRead, dependencies=[Depends(require_role("super_admin"))])
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new product.
    
    Security: Only super_admin can create.
    
    If sucursales_ids is provided, use the first one as sucursal_id for backward compatibility.
    """
    product_dict = product_data.model_dump(exclude_none=True)
    
    # Validate that at least one sucursal is provided
    if not product_dict.get("sucursales_ids") or len(product_dict.get("sucursales_ids", [])) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one sucursal must be provided in sucursales_ids"
        )
    
    # Validate product name uniqueness (excluding soft-deleted products)
    product_name = product_dict.get("name")
    if product_name:
        existing_product = await db.execute(
            select(Product).where(
                Product.name == product_name,
                Product.deleted_at.is_(None)  # Only check non-deleted products
            )
        )
        if existing_product.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product name '{product_name}' already exists"
            )
    
    # Handle multiple sucursales: use first one as sucursal_id for backward compatibility
    sucursales_ids = product_dict["sucursales_ids"]
    if sucursales_ids and len(sucursales_ids) > 0:
        # Convert to strings for JSON storage (if not already strings)
        if not isinstance(sucursales_ids[0], str):
            product_dict["sucursales_ids"] = [str(uuid_val) for uuid_val in sucursales_ids]
        else:
            product_dict["sucursales_ids"] = sucursales_ids
        
        # Use first sucursal_id as the primary one for backward compatibility
        if not product_dict.get("sucursal_id"):
            # Convert string UUID to UUID object for the foreign key
            try:
                product_dict["sucursal_id"] = uuid.UUID(product_dict["sucursales_ids"][0])
            except (ValueError, TypeError):
                # If conversion fails, try to use as is
                product_dict["sucursal_id"] = product_dict["sucursales_ids"][0]
    elif product_dict.get("sucursal_id"):
        # If only sucursal_id is provided (backward compatibility), also set it in sucursales_ids
        sucursal_id = product_dict["sucursal_id"]
        if isinstance(sucursal_id, str):
            product_dict["sucursales_ids"] = [sucursal_id]
        else:
            product_dict["sucursales_ids"] = [str(sucursal_id)]
    
    try:
        product = Product(**product_dict)
        db.add(product)
        await db.commit()
        await db.refresh(product)
        return product
    except IntegrityError as e:
        await db.rollback()
        # Check if it's a unique constraint violation on name
        error_str = str(e).lower()
        if "name" in error_str or "unique" in error_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product name '{product_name}' already exists"
            )
        # Re-raise if it's a different integrity error
        logger.error(f"IntegrityError creating product: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating product due to database constraint"
        )


@router.put("/products/{product_id}", response_model=ProductRead, dependencies=[Depends(require_role("super_admin"))])
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing product.
    
    Security: Only super_admin can update.
    
    If sucursales_ids is provided, use the first one as sucursal_id for backward compatibility.
    """
    try:
        product_uuid = uuid.UUID(product_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format"
        )
    
    result = await db.execute(
        select(Product).where(
            Product.id == product_uuid,
            Product.deleted_at.is_(None)  # Only allow updating non-deleted products
        )
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Update only provided fields
    update_data = product_data.model_dump(exclude_unset=True)
    
    # Validate product name uniqueness if name is being changed
    if "name" in update_data and update_data["name"] != product.name:
        new_name = update_data["name"]
        existing_product = await db.execute(
            select(Product).where(
                Product.name == new_name,
                Product.deleted_at.is_(None),  # Only check non-deleted products
                Product.id != product_uuid  # Exclude current product
            )
        )
        if existing_product.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product name '{new_name}' already exists"
            )
    
    # Handle multiple sucursales: use first one as sucursal_id for backward compatibility
    if "sucursales_ids" in update_data and update_data["sucursales_ids"]:
        # Convert UUIDs (may be strings from frontend) to strings for JSON storage
        sucursales_ids = update_data["sucursales_ids"]
        if sucursales_ids and len(sucursales_ids) > 0:
            if isinstance(sucursales_ids[0], str):
                # Already strings, use as is
                update_data["sucursales_ids"] = sucursales_ids
            else:
                # UUID objects, convert to strings
                update_data["sucursales_ids"] = [str(uuid_val) for uuid_val in sucursales_ids]
            # Use first sucursal_id as the primary one for backward compatibility
            if "sucursal_id" not in update_data:
                # Convert string UUID to UUID object for the foreign key
                try:
                    update_data["sucursal_id"] = uuid.UUID(update_data["sucursales_ids"][0])
                except (ValueError, TypeError):
                    # If conversion fails, try to use as is
                    update_data["sucursal_id"] = update_data["sucursales_ids"][0]
    elif "sucursal_id" in update_data and update_data["sucursal_id"]:
        # If only sucursal_id is provided, also set it in sucursales_ids
        sucursal_id = update_data["sucursal_id"]
        if isinstance(sucursal_id, str):
            update_data["sucursales_ids"] = [sucursal_id]
        else:
            update_data["sucursales_ids"] = [str(sucursal_id)]
    
    try:
        for key, value in update_data.items():
            setattr(product, key, value)
        
        await db.commit()
        await db.refresh(product)
        return product
    except IntegrityError as e:
        await db.rollback()
        # Check if it's a unique constraint violation on name
        error_str = str(e).lower()
        if "name" in error_str or "unique" in error_str:
            new_name = update_data.get("name", product.name)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product name '{new_name}' already exists"
            )
        # Re-raise if it's a different integrity error
        logger.error(f"IntegrityError updating product: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating product due to database constraint"
        )


@router.delete("/products/{product_id}", dependencies=[Depends(require_role("super_admin"))])
async def delete_product(
    product_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete (soft delete) a product.
    
    Security: Only super_admin can delete.
    
    This performs a soft delete by marking the product with deleted_at timestamp.
    The product will be permanently deleted after 30 days by an automatic cleanup task.
    """
    try:
        product_uuid = uuid.UUID(product_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format"
        )
    
    result = await db.execute(
        select(Product).where(
            Product.id == product_uuid,
            Product.deleted_at.is_(None)  # Only allow deleting non-deleted products
        )
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or already deleted"
        )
    
    # Soft delete: mark with deleted_at timestamp (also sets active=False)
    product.soft_delete()
    await db.commit()
    
    return {"message": "Product deleted successfully. It will be permanently removed after 30 days."}


# ========== SERVICES ==========

@router.get("/services", response_model=List[ServiceRead], dependencies=[Depends(require_role(["super_admin", "admin_viewer", "recepcion", "monitor"]))])
async def get_services(
    sucursal_id: str = Query(None, description="Optional: Filter by sucursal ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get services.
    If sucursal_id is provided, filter by sucursal.
    
    Filtering logic:
    - Only returns services that are not soft-deleted (deleted_at IS NULL)
    - Services where sucursal_id matches (backward compatibility)
    - OR services where sucursales_ids JSON array contains the sucursal_id
    
    Security: super_admin, admin_viewer, and recepcion can view.
    """
    query = select(Service).where(Service.deleted_at.is_(None))  # Exclude soft-deleted services
    if sucursal_id:
        try:
            sucursal_uuid = uuid.UUID(sucursal_id)
            sucursal_id_str = str(sucursal_uuid)
            
            # Hybrid filtering: sucursal_id OR sucursales_ids contains
            # Using PostgreSQL JSON functions compatible with JSON (not JSONB)
            # We need to handle NULL and empty arrays safely
            # Using a correlated subquery that references the outer query's table
            
            # Build condition using SQLAlchemy's text() with correlated subquery
            # The subquery references the outer table using the table name
            # Using COALESCE to handle NULL values and checking for non-empty arrays
            # Note: This uses a correlated subquery that references the outer query's Service table
            sucursal_id_condition = text(
                """
                EXISTS (
                    SELECT 1 
                    FROM json_array_elements_text(
                        COALESCE(services.sucursales_ids::text::json, '[]'::json)
                    ) AS elem 
                    WHERE trim(both '"' from elem::text) = :sucursal_id_str
                )
                """
            ).bindparams(sucursal_id_str=sucursal_id_str)
            
            query = query.where(
                or_(
                    # Primary sucursal_id match (backward compatibility)
                    Service.sucursal_id == sucursal_uuid,
                    # Check if sucursales_ids array contains the sucursal_id
                    # Only check if sucursales_ids is not NULL and not empty
                    and_(
                        Service.sucursales_ids.isnot(None),
                        # Check that array is not empty using json_array_length
                        text("json_array_length(COALESCE(services.sucursales_ids::text::json, '[]'::json)) > 0"),
                        sucursal_id_condition
                    )
                )
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid sucursal ID format"
            )
    result = await db.execute(query)
    services = result.scalars().all()
    services_list = list(services)
    
    # Logging for debugging (only in development/debug mode)
    if sucursal_id:
        logger.info(f"Found {len(services_list)} services for sucursal_id={sucursal_id}")
        if len(services_list) == 0:
            logger.warning(f"No services found for sucursal_id={sucursal_id} - this might indicate a filtering issue")
        elif logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Services found: {[s.name for s in services_list[:5]]}")  # Log first 5 names
    
    return services_list


@router.post("/services", response_model=ServiceRead, dependencies=[Depends(require_role("super_admin"))])
async def create_service(
    service_data: ServiceCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new service.
    
    Security: Only super_admin can create.
    
    If sucursales_ids is provided, use the first one as sucursal_id for backward compatibility.
    """
    service_dict = service_data.model_dump(exclude_none=True)
    
    # Validate that at least one sucursal is provided
    if not service_dict.get("sucursales_ids") and not service_dict.get("sucursal_id"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either sucursal_id or sucursales_ids must be provided"
        )
    
    # Validate service name uniqueness (excluding soft-deleted services)
    service_name = service_dict.get("name")
    if service_name:
        existing_service = await db.execute(
            select(Service).where(
                Service.name == service_name,
                Service.deleted_at.is_(None)  # Only check non-deleted services
            )
        )
        if existing_service.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Service name '{service_name}' already exists"
            )
    
    # Handle multiple sucursales: use first one as sucursal_id for backward compatibility
    if service_dict.get("sucursales_ids") and len(service_dict["sucursales_ids"]) > 0:
        # Convert UUIDs (may be strings from frontend) to strings for JSON storage
        sucursales_ids = service_dict["sucursales_ids"]
        if sucursales_ids and len(sucursales_ids) > 0:
            if isinstance(sucursales_ids[0], str):
                # Already strings, use as is
                service_dict["sucursales_ids"] = sucursales_ids
            else:
                # UUID objects, convert to strings
                service_dict["sucursales_ids"] = [str(uuid_val) for uuid_val in sucursales_ids]
            # Use first sucursal_id as the primary one for backward compatibility
            if not service_dict.get("sucursal_id"):
                # Convert string UUID to UUID object for the foreign key
                try:
                    service_dict["sucursal_id"] = uuid.UUID(service_dict["sucursales_ids"][0])
                except (ValueError, TypeError):
                    # If conversion fails, try to use as is
                    service_dict["sucursal_id"] = service_dict["sucursales_ids"][0]
    elif service_dict.get("sucursal_id"):
        # If only sucursal_id is provided, also set it in sucursales_ids
        sucursal_id = service_dict["sucursal_id"]
        if isinstance(sucursal_id, str):
            service_dict["sucursales_ids"] = [sucursal_id]
        else:
            service_dict["sucursales_ids"] = [str(sucursal_id)]
    
    try:
        service = Service(**service_dict)
        db.add(service)
        await db.commit()
        await db.refresh(service)
        return service
    except IntegrityError as e:
        await db.rollback()
        # Check if it's a unique constraint violation on name
        error_str = str(e).lower()
        if "name" in error_str or "unique" in error_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Service name '{service_name}' already exists"
            )
        # Re-raise if it's a different integrity error
        logger.error(f"IntegrityError creating service: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating service due to database constraint"
        )


@router.put("/services/{service_id}", response_model=ServiceRead, dependencies=[Depends(require_role("super_admin"))])
async def update_service(
    service_id: str,
    service_data: ServiceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing service.
    
    Security: Only super_admin can update.
    
    If sucursales_ids is provided, use the first one as sucursal_id for backward compatibility.
    """
    try:
        service_uuid = uuid.UUID(service_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid service ID format"
        )
    
    result = await db.execute(
        select(Service).where(
            Service.id == service_uuid,
            Service.deleted_at.is_(None)  # Only allow updating non-deleted services
        )
    )
    service = result.scalar_one_or_none()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Update only provided fields
    update_data = service_data.model_dump(exclude_unset=True)
    
    # Log what fields are being updated (for debugging)
    logger.info(f"Updating service {service_id} with fields: {list(update_data.keys())}")
    if "duration_prices" in update_data:
        logger.debug(f"duration_prices (before merge): {update_data['duration_prices']}")
    if "alerts_config" in update_data:
        logger.debug(f"alerts_config (before merge): {update_data['alerts_config']}")
    
    # Get existing service data as dict for intelligent merging
    existing_service_data = {
        "name": service.name,
        "durations_allowed": service.durations_allowed or [],
        "duration_prices": service.duration_prices or {},
        "alerts_config": service.alerts_config or [],
        "active": service.active,
        "sucursal_id": str(service.sucursal_id) if service.sucursal_id else None,
        "sucursales_ids": service.sucursales_ids or [],
    }
    
    # Apply intelligent merge for dict/list fields
    # duration_prices: merge (keep existing keys, update/override with new ones)
    # alerts_config: replace (lists are replaced by default)
    merge_config = {
        "duration_prices": True,  # Merge dict
        "alerts_config": False,   # Replace list
    }
    
    merged_update_data = apply_intelligent_update(
        update_data,
        existing_service_data,
        merge_fields=merge_config
    )
    
    # Log merged data for debugging
    if "duration_prices" in merged_update_data:
        logger.debug(f"duration_prices (after merge): {merged_update_data['duration_prices']}")
    if "alerts_config" in merged_update_data:
        logger.debug(f"alerts_config (after merge): {merged_update_data['alerts_config']}")
    
    # Validate duration_prices consistency with durations_allowed
    # Only validate if durations_allowed is being updated OR if duration_prices is being updated
    if "durations_allowed" in merged_update_data or "duration_prices" in merged_update_data:
        from utils.json_normalizers import normalize_json_int_keys
        
        durations_to_check = merged_update_data.get("durations_allowed", service.durations_allowed)
        # Get duration_prices (from update_data or existing service), normalize keys to int
        raw_duration_prices = merged_update_data.get("duration_prices", service.duration_prices)
        duration_prices_to_check = normalize_json_int_keys(raw_duration_prices)
        
        if durations_to_check and len(durations_to_check) > 0:
            if not duration_prices_to_check or len(duration_prices_to_check) == 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="duration_prices must be provided for all durations in durations_allowed"
                )
            # Check that all durations have prices (using normalized keys)
            missing_prices = [d for d in durations_to_check if d not in duration_prices_to_check or duration_prices_to_check[d] <= 0]
            if missing_prices:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Missing or invalid prices for durations: {missing_prices}"
                )
    
    # Use merged data for the rest of the update
    update_data = merged_update_data
    
    # Validate service name uniqueness if name is being changed
    if "name" in update_data and update_data["name"] != service.name:
        new_name = update_data["name"]
        existing_service = await db.execute(
            select(Service).where(
                Service.name == new_name,
                Service.deleted_at.is_(None),  # Only check non-deleted services
                Service.id != service_uuid  # Exclude current service
            )
        )
        if existing_service.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Service name '{new_name}' already exists"
            )
    
    # Handle multiple sucursales: use first one as sucursal_id for backward compatibility
    if "sucursales_ids" in update_data and update_data["sucursales_ids"]:
        # Convert UUIDs (may be strings from frontend) to strings for JSON storage
        sucursales_ids = update_data["sucursales_ids"]
        if sucursales_ids and len(sucursales_ids) > 0:
            if isinstance(sucursales_ids[0], str):
                # Already strings, use as is
                update_data["sucursales_ids"] = sucursales_ids
            else:
                # UUID objects, convert to strings
                update_data["sucursales_ids"] = [str(uuid_val) for uuid_val in sucursales_ids]
            # Use first sucursal_id as the primary one for backward compatibility
            if "sucursal_id" not in update_data:
                # Convert string UUID to UUID object for the foreign key
                try:
                    update_data["sucursal_id"] = uuid.UUID(update_data["sucursales_ids"][0])
                except (ValueError, TypeError):
                    # If conversion fails, try to use as is
                    update_data["sucursal_id"] = update_data["sucursales_ids"][0]
    elif "sucursal_id" in update_data and update_data["sucursal_id"]:
        # If only sucursal_id is provided, also set it in sucursales_ids
        sucursal_id = update_data["sucursal_id"]
        if isinstance(sucursal_id, str):
            update_data["sucursales_ids"] = [sucursal_id]
        else:
            update_data["sucursales_ids"] = [str(sucursal_id)]
    
    try:
        # Apply updates to service model
        for key, value in update_data.items():
            # Handle sucursales_ids and sucursal_id separately (already handled above)
            if key == "sucursales_ids":
                # Set sucursales_ids (already converted to strings if needed)
                service.sucursales_ids = value
            elif key == "sucursal_id":
                # Set sucursal_id (already converted to UUID if needed)
                service.sucursal_id = value
            else:
                # Set other fields normally
                setattr(service, key, value)
        
        await db.commit()
        await db.refresh(service)
        logger.info(f"Service {service_id} updated successfully")
        return service
    except IntegrityError as e:
        await db.rollback()
        # Check if it's a unique constraint violation on name
        error_str = str(e).lower()
        if "name" in error_str or "unique" in error_str:
            new_name = update_data.get("name", service.name)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Service name '{new_name}' already exists"
            )
        # Re-raise if it's a different integrity error
        logger.error(f"IntegrityError updating service: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating service due to database constraint"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error updating service {service_id}: {type(e).__name__}: {e}")
        # Re-raise to let FastAPI handle it
        raise


@router.delete("/services/{service_id}", dependencies=[Depends(require_role("super_admin"))])
async def delete_service(
    service_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete (soft delete) a service.
    
    Security: Only super_admin can delete.
    
    This performs a soft delete by marking the service with deleted_at timestamp.
    The service will be permanently deleted after 30 days by an automatic cleanup task.
    """
    try:
        service_uuid = uuid.UUID(service_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid service ID format"
        )
    
    result = await db.execute(
        select(Service).where(
            Service.id == service_uuid,
            Service.deleted_at.is_(None)  # Only allow deleting non-deleted services
        )
    )
    service = result.scalar_one_or_none()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found or already deleted"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service is already deleted"
        )
    
    # Soft delete: mark with deleted_at timestamp (also sets active=False)
    service.soft_delete()
    await db.commit()
    
    return {"message": "Service deleted successfully. It will be permanently removed after 30 days."}


# ========== PACKAGES ==========

@router.get("/packages", response_model=List[PackageRead], dependencies=[Depends(require_role(["super_admin", "admin_viewer", "recepcion", "kidibar", "monitor"]))])
async def get_packages(
    sucursal_id: str = Query(None, description="Optional: Filter by sucursal ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get packages.
    If sucursal_id is provided, filter by sucursal.
    
    Security: super_admin, admin_viewer, recepcion, and kidibar can view.
    - recepcion views service packages (filtered in frontend)
    - kidibar views product packages (filtered in frontend)
    """
    query = select(Package)
    if sucursal_id:
        try:
            sucursal_uuid = uuid.UUID(sucursal_id)
            query = query.where(Package.sucursal_id == sucursal_uuid)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid sucursal ID format"
            )
    if sucursal_id:
        try:
            sucursal_uuid = uuid.UUID(sucursal_id)
            sucursal_id_str = str(sucursal_uuid)
            
            # Hybrid filtering: sucursal_id OR sucursales_ids contains
            # Using PostgreSQL JSON functions compatible with JSON (not JSONB)
            # We need to handle NULL and empty arrays safely
            sucursal_id_condition = text(
                """
                EXISTS (
                    SELECT 1 
                    FROM json_array_elements_text(
                        COALESCE(packages.sucursales_ids::text::json, '[]'::json)
                    ) AS elem 
                    WHERE trim(both '"' from elem::text) = :sucursal_id_str
                )
                """
            ).bindparams(sucursal_id_str=sucursal_id_str)
            
            query = query.where(
                or_(
                    # Primary sucursal_id match (backward compatibility)
                    Package.sucursal_id == sucursal_uuid,
                    # Check if sucursales_ids array contains the sucursal_id
                    # Only check if sucursales_ids is not NULL and not empty
                    and_(
                        Package.sucursales_ids.isnot(None),
                        # Check that array is not empty using json_array_length
                        text("json_array_length(COALESCE(packages.sucursales_ids::text::json, '[]'::json)) > 0"),
                        sucursal_id_condition
                    )
                )
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid sucursal ID format"
            )
    query = query.where(Package.active == True)  # Only active packages
    result = await db.execute(query)
    packages = result.scalars().all()
    return list(packages)


def _serialize_package_items(items: list) -> list:
    """Convert UUID objects to strings in package items for JSON serialization."""
    serialized = []
    for item in items:
        serialized_item = {}
        if item.get("product_id"):
            serialized_item["product_id"] = str(item["product_id"])
        if item.get("service_id"):
            serialized_item["service_id"] = str(item["service_id"])
        if item.get("quantity") is not None:
            serialized_item["quantity"] = item["quantity"]
        if item.get("duration_minutes") is not None:
            serialized_item["duration_minutes"] = item["duration_minutes"]
        serialized.append(serialized_item)
    return serialized


@router.post("/packages", response_model=PackageRead, dependencies=[Depends(require_role("super_admin"))])
async def create_package(
    package_data: PackageCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new package.
    
    Security: Only super_admin can create.
    
    If sucursales_ids is provided, use the first one as sucursal_id for backward compatibility.
    """
    # Validate included_items
    # Note: Basic validation (product_id/quantity, service_id/duration_minutes) is automatic via @model_validator
    # We only need to validate business rules that require DB access (e.g., duration_minutes in service's allowed durations)
    if package_data.included_items:
        for item in package_data.included_items:
            # Validate duration_minutes is in service's durations_allowed (requires DB access)
            if item.service_id and item.duration_minutes:
                result = await db.execute(select(Service).where(Service.id == item.service_id))
                service = result.scalar_one_or_none()
                if not service:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Service with ID {item.service_id} not found"
                    )
                if item.duration_minutes not in (service.durations_allowed or []):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Duration {item.duration_minutes} not allowed for service '{service.name}'. Allowed durations: {service.durations_allowed}"
                    )
    
    package_dict = package_data.model_dump(exclude_none=True)
    
    # Validate that at least one sucursal is provided
    if not package_dict.get("sucursales_ids") or len(package_dict.get("sucursales_ids", [])) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one sucursal must be provided in sucursales_ids"
        )
    
    # Handle multiple sucursales: use first one as sucursal_id for backward compatibility
    sucursales_ids = package_dict["sucursales_ids"]
    if sucursales_ids and len(sucursales_ids) > 0:
        # Convert to strings for JSON storage (if not already strings)
        if not isinstance(sucursales_ids[0], str):
            package_dict["sucursales_ids"] = [str(uuid_val) for uuid_val in sucursales_ids]
        else:
            package_dict["sucursales_ids"] = sucursales_ids
        
        # Use first sucursal_id as the primary one for backward compatibility
        if not package_dict.get("sucursal_id"):
            # Convert string UUID to UUID object for the foreign key
            try:
                package_dict["sucursal_id"] = uuid.UUID(package_dict["sucursales_ids"][0])
            except (ValueError, TypeError):
                # If conversion fails, try to use as is
                package_dict["sucursal_id"] = package_dict["sucursales_ids"][0]
    elif package_dict.get("sucursal_id"):
        # If only sucursal_id is provided (backward compatibility), also set it in sucursales_ids
        sucursal_id = package_dict["sucursal_id"]
        if isinstance(sucursal_id, str):
            package_dict["sucursales_ids"] = [sucursal_id]
        else:
            package_dict["sucursales_ids"] = [str(sucursal_id)]
    
    # Serialize UUIDs in included_items to strings for JSON storage
    if package_dict.get("included_items"):
        package_dict["included_items"] = _serialize_package_items(package_dict["included_items"])
    
    try:
        package = Package(**package_dict)
        db.add(package)
        await db.commit()
        await db.refresh(package)
        return package
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"IntegrityError creating package: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating package due to database constraint"
        )


@router.put("/packages/{package_id}", response_model=PackageRead, dependencies=[Depends(require_role("super_admin"))])
async def update_package(
    package_id: str,
    package_data: PackageUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing package.
    
    Security: Only super_admin can update.
    """
    try:
        package_uuid = uuid.UUID(package_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid package ID format"
        )
    
    result = await db.execute(select(Package).where(Package.id == package_uuid))
    package = result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    # Update only provided fields
    update_data = package_data.model_dump(exclude_unset=True)
    
    # Validate included_items if provided (automatic validation via @model_validator)
    # Note: Basic validation (product_id/quantity, service_id/duration_minutes) is automatic
    # We only need to validate business rules that require DB access (e.g., duration_minutes in service's allowed durations)
    if "included_items" in update_data and update_data["included_items"]:
        # Convert dict items to PackageItem instances for automatic validation
        from schemas.package import PackageItem
        validated_items = []
        for item_dict in update_data["included_items"]:
            # This will automatically validate via @model_validator
            try:
                validated_item = PackageItem(**item_dict)
                validated_items.append(validated_item)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid package item: {str(e)}"
                )
        
        # Validate business rules that require DB access
        for item in validated_items:
            if item.service_id and item.duration_minutes:
                try:
                    service_id = uuid.UUID(item.service_id) if isinstance(item.service_id, str) else item.service_id
                except (ValueError, TypeError):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid service_id format: {item.service_id}"
                    )
                result = await db.execute(select(Service).where(Service.id == service_id))
                service = result.scalar_one_or_none()
                if not service:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Service with ID {service_id} not found"
                    )
                if item.duration_minutes not in (service.durations_allowed or []):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Duration {item.duration_minutes} not allowed for service '{service.name}'. Allowed durations: {service.durations_allowed}"
                    )
        
        # Replace with validated items (convert back to dict for storage)
        update_data["included_items"] = [item.model_dump() for item in validated_items]
    
    # Handle multiple sucursales: use first one as sucursal_id for backward compatibility
    if "sucursales_ids" in update_data and update_data["sucursales_ids"]:
        # Convert UUIDs (may be strings from frontend) to strings for JSON storage
        sucursales_ids = update_data["sucursales_ids"]
        if sucursales_ids and len(sucursales_ids) > 0:
            # Convert to strings if needed
            if not isinstance(sucursales_ids[0], str):
                update_data["sucursales_ids"] = [str(uuid_val) for uuid_val in sucursales_ids]
            else:
                update_data["sucursales_ids"] = sucursales_ids
            
            # Use first sucursal_id as the primary one for backward compatibility
            try:
                update_data["sucursal_id"] = uuid.UUID(update_data["sucursales_ids"][0])
            except (ValueError, TypeError):
                # If conversion fails, try to use as is
                update_data["sucursal_id"] = update_data["sucursales_ids"][0]
    elif "sucursal_id" in update_data and update_data["sucursal_id"]:
        # If only sucursal_id is provided (backward compatibility), also set it in sucursales_ids
        sucursal_id = update_data["sucursal_id"]
        if isinstance(sucursal_id, str):
            update_data["sucursales_ids"] = [sucursal_id]
        else:
            update_data["sucursales_ids"] = [str(sucursal_id)]
    
    # Serialize UUIDs in included_items to strings for JSON storage
    if "included_items" in update_data:
        update_data["included_items"] = _serialize_package_items(update_data["included_items"])
    for key, value in update_data.items():
        setattr(package, key, value)
    
    await db.commit()
    await db.refresh(package)
    return package


@router.delete("/packages/{package_id}", dependencies=[Depends(require_role("super_admin"))])
async def delete_package(
    package_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete (soft delete) an existing package.
    
    Security: Only super_admin can delete.
    """
    try:
        package_uuid = uuid.UUID(package_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid package ID format"
        )
    
    result = await db.execute(select(Package).where(Package.id == package_uuid))
    package = result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    # Soft delete: set active to False
    package.active = False
    await db.commit()
    
    return {"message": "Package deleted successfully"}

