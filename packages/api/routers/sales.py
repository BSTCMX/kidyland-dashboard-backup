"""
Sales endpoints.

Security Rules:
- Only recepcion and kidibar roles can CREATE sales
- recepcion can create service and package sales
- kidibar can create product sales
- All authenticated users can READ sales (filtered by their sucursal if applicable)
"""
import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from database import get_db
from schemas.sale import SaleCreate, SaleRead, TimerExtensionRequest
from schemas.sale_item import SaleItemRead
from schemas.timer import TimerRead
from models.user import User
from models.sale import Sale
from models.sale_item import SaleItem
from models.package import Package
from models.day_start import DayStart
from services.sale_service import SaleService
from services.day_start_service import DayStartService
from utils.auth import require_role, get_current_user
from utils.sale_serializers import serialize_sale_for_frontend, serialize_sales_for_frontend
from utils.package_helpers import get_service_package_ids, get_product_package_ids
from typing import Dict, Any, List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sales", tags=["sales"])


async def require_active_day(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DayStart:
    """
    Dependency to ensure the day is active before allowing sales.
    
    This validates that a day has been started for the user's sucursal
    before allowing any sales operations.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Active DayStart object
        
    Raises:
        HTTPException: If day is not active (403) or user has no sucursal (400)
    """
    # Get user's sucursal_id
    sucursal_id = current_user.sucursal_id
    if not sucursal_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario debe tener sucursal_id asignado para realizar ventas."
        )
    
    # Check if day is active
    active_day = await DayStartService.get_active_day(db, str(sucursal_id))
    if not active_day:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "No se puede realizar ventas. El día no ha sido iniciado. "
                "Por favor, inicie el día desde la sección de Reportes antes de realizar ventas."
            )
        )
    
    return active_day


@router.post("", response_model=Dict[str, Any], dependencies=[
    Depends(require_role(["recepcion", "kidibar"])),
    Depends(require_active_day)  # Validate day is active before allowing sales
])
async def create_sale(
    sale_data: SaleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new sale.
    
    Security: Only recepcion and kidibar roles can create sales.
    
    For service sales, automatically creates a timer.
    Validates payment method and required fields.
    
    Returns:
        Dictionary with sale_id, timer_id (nullable), sale object, timer object (nullable)
    """
    try:
        result = await SaleService.create_sale(
            db=db,
            sale_data=sale_data,
            current_user=current_user
        )
        
        # Service already returns serialized dicts, so we can return directly
        return result
        
    except ValueError as e:
        logger.warning(f"Validation error creating sale: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating sale: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating sale"
        )


@router.get("")
async def get_sales(
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(25, ge=1, le=500, description="Maximum number of records to return (1-500, default: 25)"),
    sucursal_id: Optional[str] = Query(None, description="Filter by sucursal ID"),
    start_date: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    tipo: Optional[str] = Query(None, description="Filter by sale type (service, product, package)"),
    package_type: Optional[str] = Query(None, description="Filter package sales by package type (service, product). Only valid when tipo='package'"),
    include_package_type: Optional[str] = Query(None, description="Include package sales of specified type along with tipo filter. Example: tipo='product' + include_package_type='product' returns both product sales and product packages"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get paginated list of sales with optional filters.
    
    Security: All authenticated users can read sales.
    Users with sucursal_id are automatically filtered to their sucursal.
    
    Package filtering:
    - When tipo='package' and package_type is provided, filters packages by their content type
    - package_type='service': only service packages (packages containing only services)
    - package_type='product': only product packages (packages containing only products)
    
    Returns:
        List of SaleRead objects (paginated)
    """
    try:
        # Validate package_type parameter
        if package_type and tipo != "package":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="package_type parameter is only valid when tipo='package'"
            )
        
        if package_type and package_type not in ["service", "product"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="package_type must be 'service' or 'product'"
            )
        
        # Validate include_package_type parameter
        if include_package_type and include_package_type not in ["service", "product"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="include_package_type must be 'service' or 'product'"
            )
        
        if include_package_type and tipo and tipo not in ["service", "product"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="include_package_type is only valid when tipo='service' or tipo='product'"
            )
        
        # Build query with selectinload to avoid N+1 queries
        query = select(Sale).options(selectinload(Sale.items))
        
        # Filter by sucursal_id
        # If user has sucursal_id, filter by it (unless explicitly overridden)
        if current_user.sucursal_id:
            filter_sucursal_id = UUID(sucursal_id) if sucursal_id else current_user.sucursal_id
            query = query.where(Sale.sucursal_id == filter_sucursal_id)
        elif sucursal_id:
            # User doesn't have sucursal_id but provided one (super_admin/admin_viewer)
            query = query.where(Sale.sucursal_id == UUID(sucursal_id))
        # If no sucursal_id filter and user has no sucursal_id, show all (super_admin)
        
        # Filter by tipo and package_type (Patrón A: Subconsulta con IN clause)
        # Also handle include_package_type for unified product/service + package views
        tipo_conditions = []
        
        if tipo == "package" and package_type:
            # Get sucursal UUID for package filtering
            if current_user.sucursal_id:
                filter_sucursal_uuid = UUID(sucursal_id) if sucursal_id else current_user.sucursal_id
            elif sucursal_id:
                filter_sucursal_uuid = UUID(sucursal_id)
            else:
                # If no sucursal filter, we can't filter packages by type efficiently
                # This case should be rare (super_admin viewing all)
                filter_sucursal_uuid = None
            
            if filter_sucursal_uuid:
                # Step 1: Get all package sales for this sucursal (within date range if provided)
                package_sales_subquery = select(SaleItem.ref_id.label("package_id")).join(
                    Sale, SaleItem.sale_id == Sale.id
                ).where(
                    and_(
                        SaleItem.type == "package",
                        Sale.tipo == "package",
                        Sale.sucursal_id == filter_sucursal_uuid
                    )
                )
                
                # Add date filters to subquery if provided
                if start_date:
                    try:
                        if "T" in start_date or "Z" in start_date:
                            start_datetime = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                        else:
                            start_datetime = datetime.fromisoformat(start_date)
                            start_datetime = start_datetime.replace(tzinfo=timezone.utc)
                        if start_datetime.tzinfo is None:
                            start_datetime = start_datetime.replace(tzinfo=timezone.utc)
                        package_sales_subquery = package_sales_subquery.where(Sale.created_at >= start_datetime)
                    except ValueError:
                        pass  # Will be caught later
                
                if end_date:
                    try:
                        if "T" in end_date or "Z" in end_date:
                            end_datetime = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                        else:
                            end_datetime = datetime.fromisoformat(end_date)
                            end_datetime = end_datetime.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                        if end_datetime.tzinfo is None:
                            end_datetime = end_datetime.replace(tzinfo=timezone.utc)
                        package_sales_subquery = package_sales_subquery.where(Sale.created_at <= end_datetime)
                    except ValueError:
                        pass  # Will be caught later
                
                # Execute subquery to get package IDs
                package_sales_result = await db.execute(package_sales_subquery)
                package_sales_rows = package_sales_result.all()
                package_ids = list(set(row.package_id for row in package_sales_rows))
                
                # Step 2: Load packages and filter by type
                if package_ids:
                    packages_query = select(Package).where(Package.id.in_(package_ids))
                    packages_result = await db.execute(packages_query)
                    packages = packages_result.scalars().all()
                    
                    # Step 3: Get filtered package IDs using helpers
                    if package_type == "service":
                        filtered_package_ids = get_service_package_ids(list(packages))
                    else:  # package_type == "product"
                        filtered_package_ids = get_product_package_ids(list(packages))
                    
                    # Step 4: Filter sales by filtered package IDs using SaleItem
                    if filtered_package_ids:
                        # Use subquery to find sales that have items with filtered package IDs
                        filtered_sale_ids_subquery = select(SaleItem.sale_id).where(
                            and_(
                                SaleItem.type == "package",
                                SaleItem.ref_id.in_(filtered_package_ids)
                            )
                        ).distinct()
                        
                        query = query.where(
                            and_(
                                Sale.tipo == "package",
                                Sale.id.in_(filtered_sale_ids_subquery)
                            )
                        )
                    else:
                        # No packages of this type found, return empty result
                        query = query.where(Sale.id == None)  # This will return no results
                else:
                    # No package sales found, return empty result
                    query = query.where(Sale.id == None)  # This will return no results
            else:
                # No sucursal filter, can't efficiently filter packages
                # Just filter by tipo (will show all packages)
                tipo_conditions.append(Sale.tipo == "package")
        elif tipo and include_package_type:
            # Unified view: tipo + packages of same type (e.g., products + product packages)
            # Get sucursal UUID for package filtering
            if current_user.sucursal_id:
                filter_sucursal_uuid = UUID(sucursal_id) if sucursal_id else current_user.sucursal_id
            elif sucursal_id:
                filter_sucursal_uuid = UUID(sucursal_id)
            else:
                filter_sucursal_uuid = None
            
            # Add base tipo condition
            tipo_conditions.append(Sale.tipo == tipo)
            
            if filter_sucursal_uuid:
                # Get package IDs for the specified type
                # Step 1: Get all package sales for this sucursal
                package_sales_subquery = select(SaleItem.ref_id.label("package_id")).join(
                    Sale, SaleItem.sale_id == Sale.id
                ).where(
                    and_(
                        SaleItem.type == "package",
                        Sale.tipo == "package",
                        Sale.sucursal_id == filter_sucursal_uuid
                    )
                )
                
                # Execute subquery to get package IDs
                package_sales_result = await db.execute(package_sales_subquery)
                package_sales_rows = package_sales_result.all()
                package_ids = list(set(row.package_id for row in package_sales_rows))
                
                # Step 2: Load packages and filter by type
                if package_ids:
                    packages_query = select(Package).where(Package.id.in_(package_ids))
                    packages_result = await db.execute(packages_query)
                    packages = packages_result.scalars().all()
                    
                    # Step 3: Get filtered package IDs using helpers
                    if include_package_type == "service":
                        filtered_package_ids = get_service_package_ids(list(packages))
                    else:  # include_package_type == "product"
                        filtered_package_ids = get_product_package_ids(list(packages))
                    
                    # Step 4: Add condition for package sales of the specified type
                    if filtered_package_ids:
                        filtered_sale_ids_subquery = select(SaleItem.sale_id).where(
                            and_(
                                SaleItem.type == "package",
                                SaleItem.ref_id.in_(filtered_package_ids)
                            )
                        ).distinct()
                        
                        tipo_conditions.append(
                            Sale.id.in_(filtered_sale_ids_subquery)
                        )
        
        # Apply tipo conditions
        if tipo_conditions:
            if len(tipo_conditions) == 1:
                query = query.where(tipo_conditions[0])
            else:
                # OR condition: tipo OR packages of same type
                query = query.where(or_(*tipo_conditions))
        elif tipo:
            # Simple tipo filter (no package_type or include_package_type specified)
            query = query.where(Sale.tipo == tipo)
        
        # Filter by date range
        if start_date:
            try:
                # Try parsing as ISO format first
                if "T" in start_date or "Z" in start_date:
                    start_datetime = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                else:
                    # Parse as YYYY-MM-DD and set to start of day in UTC
                    start_datetime = datetime.fromisoformat(start_date)
                    start_datetime = start_datetime.replace(tzinfo=timezone.utc)
                
                if start_datetime.tzinfo is None:
                    # If naive, assume UTC
                    start_datetime = start_datetime.replace(tzinfo=timezone.utc)
                query = query.where(Sale.created_at >= start_datetime)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid start_date format. Use YYYY-MM-DD or ISO format."
                )
        
        if end_date:
            try:
                # Try parsing as ISO format first
                if "T" in end_date or "Z" in end_date:
                    end_datetime = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                else:
                    # Parse as YYYY-MM-DD and set to end of day in UTC
                    end_datetime = datetime.fromisoformat(end_date)
                    end_datetime = end_datetime.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                
                if end_datetime.tzinfo is None:
                    # If naive, assume UTC
                    end_datetime = end_datetime.replace(tzinfo=timezone.utc)
                else:
                    # Ensure end of day if it's just a date
                    if "T" not in end_date and "Z" not in end_date:
                        end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
                query = query.where(Sale.created_at <= end_datetime)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid end_date format. Use YYYY-MM-DD or ISO format."
                )
        
        # Order by created_at descending (newest first)
        query = query.order_by(Sale.created_at.desc())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        sales = result.scalars().all()
        
        logger.debug(
            f"Retrieved {len(sales)} sales (skip={skip}, limit={limit}, "
            f"sucursal_id={sucursal_id}, tipo={tipo})"
        )
        
        # Serialize to frontend-compatible format
        serialized_sales = serialize_sales_for_frontend(list(sales))
        
        return serialized_sales
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error in get_sales: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving sales: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving sales"
        )


@router.get("/{sale_id}")
async def get_sale(
    sale_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific sale by ID.
    
    Security: All authenticated users can read sales.
    Users with sucursal_id are automatically filtered to their sucursal.
    
    Returns:
        Sale object in frontend-compatible format
    """
    try:
        # Get sale with items loaded
        sale = await SaleService.get_sale_with_items(db, sale_id)
        
        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sale with ID {sale_id} not found"
            )
        
        # Check if user has access to this sale's sucursal
        # If user has sucursal_id, they can only see sales from their sucursal
        if current_user.sucursal_id and sale.sucursal_id != current_user.sucursal_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sale with ID {sale_id} not found"
            )
        
        # Serialize to frontend-compatible format
        # Wrap in try-except to catch serialization errors specifically
        try:
            serialized_sale = serialize_sale_for_frontend(sale)
        except Exception as serialize_error:
            logger.error(
                f"Error serializing sale {sale_id}: {serialize_error}",
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error serializing sale data: {str(serialize_error)}"
            )
        
        return serialized_sale
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sale {sale_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting sale: {str(e)}"
        )


@router.post("/{sale_id}/print", dependencies=[Depends(require_role(["recepcion", "kidibar", "super_admin", "admin_viewer"]))])
async def print_ticket(
    sale_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate and return HTML ticket for a sale.
    
    Security: recepcion, kidibar, super_admin, and admin_viewer can print tickets.
    
    Returns:
        HTML response with ticket content
    """
    try:
        # Convert string UUID to UUID if needed
        if isinstance(sale_id, str):
            try:
                sale_id = UUID(sale_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid sale_id format: {sale_id}"
                )
        
        # Generate HTML ticket
        html = await SaleService.generate_ticket_html(
            db=db,
            sale_id=sale_id
        )
        
        # Return HTML response
        return Response(
            content=html,
            media_type="text/html; charset=utf-8"
        )
        
    except ValueError as e:
        logger.warning(f"Error generating ticket: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating ticket: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating ticket"
        )


@router.post("/{sale_id}/extend", response_model=Dict[str, Any], dependencies=[
    Depends(require_role(["recepcion", "kidibar"])),
    Depends(require_active_day)  # Validate day is active before allowing timer extensions
])
async def extend_timer_with_sale(
    sale_id: UUID,
    extension_data: TimerExtensionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Extend a timer by creating a new sale with service extension.
    
    Security: Only recepcion and kidibar roles can extend timers.
    
    This endpoint:
    1. Gets the original sale and its timer
    2. Validates the extension duration is valid for the service
    3. Calculates price from service.duration_prices
    4. Creates a new sale with the extension item
    5. Extends the timer
    6. Clears obsolete alerts for the extended timer
    7. Returns ticket HTML with contextual message
    
    Args:
        sale_id: ID of the original sale that has the timer
        extension_data: Extension request data (duration, payment, etc.)
        
    Returns:
        Dictionary with sale_id, timer_id, sale object, timer object, and ticket_html
    """
    try:
        # Convert string UUID to UUID if needed
        if isinstance(sale_id, str):
            try:
                sale_id = UUID(sale_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid sale_id format: {sale_id}"
                )
        
        # Call service method
        result = await SaleService.extend_timer_with_sale(
            db=db,
            original_sale_id=sale_id,
            duration_minutes=extension_data.duration_minutes,
            payment_method=extension_data.payment_method,
            payer_name=extension_data.payer_name,
            payer_phone=extension_data.payer_phone,
            payer_signature=extension_data.payer_signature,
            cash_received_cents=extension_data.cash_received_cents,
            card_auth_code=extension_data.card_auth_code,
            transfer_reference=extension_data.transfer_reference,
            current_user=current_user
        )
        
        return result
        
    except ValueError as e:
        logger.warning(f"Validation error extending timer: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error extending timer: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error extending timer"
        )
