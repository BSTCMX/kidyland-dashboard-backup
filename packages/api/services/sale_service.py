"""
Sale Service - Business logic for sale operations.

Handles all sale-related business logic including:
- Sale creation with validations
- Timer creation for service sales
- Payment method validation
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID

from models.sale import Sale
from models.sale_item import SaleItem
from models.timer import Timer
from models.service import Service
from models.product import Product
from models.package import Package
from models.sucursal import Sucursal
from models.timer_history import TimerHistory
from schemas.sale import SaleCreate
from models.user import User, UserRole
from utils.datetime_helpers import format_datetime_local, format_time_local, create_local_midnight_datetime
from services.timer_alert_service import TimerAlertService
from services.day_start_service import DayStartService
from services.stock_service import StockService

logger = logging.getLogger(__name__)


class SaleService:
    """Service for handling sale management operations."""
    
    @staticmethod
    async def create_sale(
        db: AsyncSession,
        sale_data: SaleCreate,
        current_user: User
    ) -> Dict[str, Any]:
        """
        Create a new sale with validations and automatic timer creation for services.
        
        Args:
            db: Database session
            sale_data: Sale creation data
            current_user: Current authenticated user
            
        Returns:
            Dictionary with sale_id, timer_id (nullable), sale object, timer object (nullable)
            
        Raises:
            ValueError: If validation fails
        """
        # Validate user has permission (recepcion, kidibar, or super_admin)
        if current_user.role not in [UserRole.RECEPCION, UserRole.KIDIBAR, UserRole.SUPER_ADMIN]:
            raise ValueError("Only recepcion, kidibar, and super_admin roles can create sales")
        
        # Validate items exist
        if not sale_data.items or len(sale_data.items) == 0:
            raise ValueError("Sale must have at least one item")
        
        # Validate payment method
        valid_payment_methods = ["cash", "card", "transfer"]
        if sale_data.payment_method not in valid_payment_methods:
            raise ValueError(f"Invalid payment_method. Must be one of: {', '.join(valid_payment_methods)}")
        
        # Validate transfer payment requires transfer_reference
        if sale_data.payment_method == "transfer":
            if not sale_data.transfer_reference or not sale_data.transfer_reference.strip():
                raise ValueError("transfer_reference is required for transfer payment method")
        
        # Validate cash payment
        if sale_data.payment_method == "cash":
            if sale_data.cash_received_cents is None:
                raise ValueError("cash_received_cents is required for cash payment method")
            if sale_data.cash_received_cents < sale_data.total_cents:
                raise ValueError(f"cash_received_cents ({sale_data.cash_received_cents}) must be >= total_cents ({sale_data.total_cents}) for cash payments")
        
        # Validate card payment
        if sale_data.payment_method == "card":
            if not sale_data.card_auth_code or not sale_data.card_auth_code.strip():
                raise ValueError("card_auth_code is required for card payment method")
        
        # Validate items
        if not sale_data.items or len(sale_data.items) == 0:
            raise ValueError("sale_data.items is required and must not be empty")
        
        # Validate price calculations
        calculated_subtotal = sum(item.get("subtotal_cents", 0) for item in sale_data.items)
        if calculated_subtotal != sale_data.subtotal_cents:
            raise ValueError(f"subtotal_cents mismatch. Calculated: {calculated_subtotal}, provided: {sale_data.subtotal_cents}")
        
        calculated_total = sale_data.subtotal_cents - (sale_data.discount_cents or 0)
        if calculated_total != sale_data.total_cents:
            raise ValueError(f"total_cents mismatch. Calculated: {calculated_total}, provided: {sale_data.total_cents}")
        
        # Use current_user.id instead of sale_data.usuario_id (security: prevent user impersonation)
        # Use current_user.sucursal_id if user has one, otherwise use sale_data.sucursal_id
        sucursal_id = current_user.sucursal_id if current_user.sucursal_id else sale_data.sucursal_id
        
        # Validate sucursal_id is not None
        if not sucursal_id:
            raise ValueError("sucursal_id is required. User must have sucursal_id or it must be provided in sale_data")
        
        # Convert to UUID if it's a string
        if isinstance(sucursal_id, str):
            try:
                sucursal_id = UUID(sucursal_id)
            except ValueError:
                raise ValueError(f"Invalid sucursal_id format: {sucursal_id}")
        elif not isinstance(sucursal_id, UUID):
            sucursal_id = UUID(str(sucursal_id))
        
        # Note: Day validation is handled by require_active_day dependency in the router.
        # This check serves as a fallback defense-in-depth measure.
        # The primary validation happens at the FastAPI dependency level before this code executes.
        active_day = await DayStartService.get_active_day(db, str(sucursal_id))
        if not active_day:
            raise ValueError(
                "No se puede realizar ventas. El día no ha sido iniciado. "
                "Por favor, inicie el día desde la sección de Reportes antes de realizar ventas."
            )
        
        # Validate and decrement stock for product and package sales
        # Service sales don't require stock validation/decrement
        if sale_data.tipo in ["product", "package"]:
            # Validate stock availability before creating the sale
            is_valid, stock_errors = await StockService.validate_stock_availability(
                db=db,
                items=sale_data.items,
                sucursal_id=sucursal_id
            )
            
            if not is_valid:
                error_message = "Stock insuficiente para completar la venta:\n" + "\n".join(stock_errors)
                logger.warning(f"Stock validation failed for sale: {error_message}")
                raise ValueError(error_message)
            
            # Stock is available, proceed with decrement (atomic operation)
            # This will be rolled back automatically if sale creation fails
            try:
                await StockService.decrement_stock_atomic(
                    db=db,
                    items=sale_data.items,
                    sucursal_id=sucursal_id
                )
                logger.info(
                    f"Stock decremented successfully for sale type '{sale_data.tipo}' "
                    f"with {len(sale_data.items)} items"
                )
            except ValueError as e:
                # If decrement fails (e.g., race condition), rollback and raise error
                logger.error(f"Stock decrement failed: {e}")
                await db.rollback()
                raise ValueError(f"Error al actualizar el inventario: {e}")
        
        # Serialize children array to JSON if provided
        # Always store children as an array, even for single-child sales
        # This ensures consistency and allows displaying children in history
        children_json = None
        if sale_data.children is not None and len(sale_data.children) > 0:
            children_json = [
                {"name": child.name, "age": child.age}
                for child in sale_data.children
            ]
        # If children array is not provided but child_name/child_age are (legacy format),
        # create children array from legacy fields for consistency
        elif sale_data.child_name and sale_data.child_name.strip():
            children_json = [
                {"name": sale_data.child_name.strip(), "age": sale_data.child_age}
            ]
            logger.debug(f"Created children array from legacy child_name/child_age for sale")
        
        # Create Sale object
        sale_dict = {
            "sucursal_id": sucursal_id,
            "usuario_id": current_user.id,
            "tipo": sale_data.tipo,
            "subtotal_cents": sale_data.subtotal_cents,
            "discount_cents": sale_data.discount_cents or 0,
            "total_cents": sale_data.total_cents,
            "payer_name": sale_data.payer_name,
            "payer_phone": sale_data.payer_phone,
            "payer_signature": sale_data.payer_signature,
            "payment_method": sale_data.payment_method,
            "cash_received_cents": sale_data.cash_received_cents,
            "card_auth_code": sale_data.card_auth_code,
            "transfer_reference": sale_data.transfer_reference,
            "children": children_json,
        }
        
        # Add scheduled_date if provided (for package sales)
        if sale_data.scheduled_date:
            # Get sucursal timezone for proper date handling
            sucursal_result = await db.execute(
                select(Sucursal).where(Sucursal.id == sucursal_id)
            )
            sucursal = sucursal_result.scalar_one_or_none()
            timezone_str = sucursal.timezone if sucursal else "America/Mexico_City"
            
            logger.info(
                f"[SCHEDULED_DATE] Creating sale with scheduled_date: "
                f"input_date={sale_data.scheduled_date}, "
                f"sucursal_id={sucursal_id}, "
                f"sucursal_timezone={timezone_str}"
            )
            
            # Create datetime at midnight in sucursal timezone, then convert to UTC for storage
            # This ensures the date is interpreted correctly in the sucursal's timezone context
            scheduled_datetime_utc = create_local_midnight_datetime(sale_data.scheduled_date, timezone_str)
            logger.info(
                f"[SCHEDULED_DATE] Created UTC datetime: {scheduled_datetime_utc} "
                f"(represents {sale_data.scheduled_date} at midnight in {timezone_str})"
            )
            # Convert to naive datetime for storage (PostgreSQL column is timezone=False)
            # We store the UTC datetime but without timezone info, since the column doesn't support it
            # When we retrieve it, we'll treat it as UTC
            scheduled_datetime_naive = scheduled_datetime_utc.replace(tzinfo=None)
            logger.info(
                f"[SCHEDULED_DATE] Stored as naive datetime: {scheduled_datetime_naive} "
                f"(will be interpreted as UTC when retrieved)"
            )
            sale_dict["scheduled_date"] = scheduled_datetime_naive
        
        sale = Sale(**sale_dict)
        db.add(sale)
        await db.flush()  # Flush to get sale.id
        
        # Create SaleItems
        for item_data in sale_data.items:
            sale_item = SaleItem(
                sale_id=sale.id,
                type=item_data["type"],
                ref_id=UUID(item_data["ref_id"]),
                quantity=item_data.get("quantity", 1),
                unit_price_cents=item_data["unit_price_cents"],
                subtotal_cents=item_data["subtotal_cents"],
            )
            db.add(sale_item)
        
        await db.flush()  # Flush to ensure items are saved
        
        # Create Timer if this is a service sale
        timer = None
        timer_id = None
        
        if sale_data.tipo == "service":
            # Find the service item
            service_item = next(
                (item for item in sale_data.items if item.get("type") == "service"),
                None
            )
            
            if service_item:
                service_id = UUID(service_item["ref_id"])
                duration_minutes = service_item.get("duration_minutes")
                # Default delay is 3 minutes for service sales (business rule)
                start_delay_minutes = service_item.get("start_delay_minutes", 3)
                
                # Verify service exists
                service_result = await db.execute(
                    select(Service).where(Service.id == service_id)
                )
                service = service_result.scalar_one_or_none()
                
                if not service:
                    raise ValueError(f"Service with ID {service_id} not found")
                
                # Calculate entry_time and exit_time
                # entry_time = when child actually enters (now + delay minutes)
                # This is the time that gets printed on the ticket as "Hora de entrada"
                # Use timezone-aware datetime for PostgreSQL compatibility
                now = datetime.now(timezone.utc)
                entry_time = now + timedelta(minutes=start_delay_minutes)
                
                if duration_minutes:
                    # Start timer after delay
                    start_at = now + timedelta(minutes=start_delay_minutes)
                    exit_time = start_at + timedelta(minutes=duration_minutes)
                else:
                    # If no duration, set exit_time to None (day-based service)
                    start_at = None
                    exit_time = None
                
                # Get child information for timer
                # Priority: use first child from children array if available, otherwise use legacy child_name/child_age
                if sale_data.children and len(sale_data.children) > 0:
                    # Multi-child sale: use first child for timer (for compatibility with existing timer logic)
                    first_child = sale_data.children[0]
                    child_name = first_child.name
                    child_age = first_child.age
                else:
                    # Legacy single-child format
                    child_name = sale_data.child_name
                    child_age = sale_data.child_age
                
                # Create Timer
                timer = Timer(
                    sale_id=sale.id,
                    service_id=service_id,
                    start_delay_minutes=start_delay_minutes,
                    child_name=child_name,
                    child_age=child_age,
                    status="active" if start_delay_minutes == 0 else "scheduled",
                    start_at=start_at,
                    end_at=exit_time,
                    entry_time=entry_time,
                    exit_time=exit_time,
                )
                
                db.add(timer)
                await db.flush()  # Flush to get timer.id
                timer_id = str(timer.id)
        
        # Flush one more time to ensure all auto-generated fields (like timestamps) are set
        await db.flush()
        
        # Refresh objects to load auto-generated fields (timestamps, etc.)
        await db.refresh(sale)
        if timer:
            await db.refresh(timer)
        
        # Serialize objects before commit to avoid any detached instance issues
        # We refresh after flush but before commit to ensure all fields are loaded
        sale_dict_response = {
            "id": str(sale.id),
            "sucursal_id": str(sale.sucursal_id),
            "usuario_id": str(sale.usuario_id),
            "tipo": sale.tipo,
            "subtotal_cents": sale.subtotal_cents,
            "discount_cents": sale.discount_cents,
            "total_cents": sale.total_cents,
            "payer_name": sale.payer_name,
            "payer_phone": sale.payer_phone,
            "payer_signature": sale.payer_signature,
            "payment_method": sale.payment_method,
            "cash_received_cents": sale.cash_received_cents,
            "card_auth_code": sale.card_auth_code,
            "transfer_reference": sale.transfer_reference,
            "created_at": sale.created_at.isoformat() if sale.created_at else None,
            "updated_at": sale.updated_at.isoformat() if sale.updated_at else None,
        }
        
        timer_dict_response = None
        if timer:
            timer_dict_response = {
                "id": str(timer.id),
                "sale_id": str(timer.sale_id),
                "service_id": str(timer.service_id),
                "start_delay_minutes": timer.start_delay_minutes,
                "child_name": timer.child_name,
                "child_age": timer.child_age,
                "status": timer.status,
                "start_at": timer.start_at.isoformat() if timer.start_at else None,
                "end_at": timer.end_at.isoformat() if timer.end_at else None,
                "entry_time": timer.entry_time.isoformat() if timer.entry_time else None,
                "exit_time": timer.exit_time.isoformat() if timer.exit_time else None,
                "created_at": timer.created_at.isoformat() if timer.created_at else None,
                "updated_at": timer.updated_at.isoformat() if timer.updated_at else None,
            }
        
        # Commit transaction (objects are already serialized)
        await db.commit()
        
        # Build response
        response = {
            "sale_id": str(sale.id),
            "timer_id": timer_id,
            "sale": sale_dict_response,
            "timer": timer_dict_response,
        }
        
        logger.info(f"Sale created successfully: {sale.id}, Timer: {timer_id}")
        
        return response
    
    @staticmethod
    async def get_sale_with_items(
        db: AsyncSession,
        sale_id: UUID
    ) -> Optional[Sale]:
        """
        Get a sale by ID with items loaded.
        
        Args:
            db: Database session
            sale_id: Sale ID to fetch
            
        Returns:
            Sale object with items loaded, or None if not found
        """
        result = await db.execute(
            select(Sale)
            .options(selectinload(Sale.items))
            .where(Sale.id == sale_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def generate_ticket_html(
        db: AsyncSession,
        sale_id: UUID
    ) -> str:
        """
        Generate HTML for printing a sale ticket.
        
        Args:
            db: Database session
            sale_id: Sale ID to generate ticket for
            
        Returns:
            HTML string for the ticket
            
        Raises:
            ValueError: If sale not found
        """
        # Get sale with items
        sale = await SaleService.get_sale_with_items(db, sale_id)
        if not sale:
            raise ValueError(f"Sale with ID {sale_id} not found")
        
        # Log children data for debugging
        if sale.children:
            logger.debug(f"Sale {sale_id} has children data: {sale.children}")
        else:
            logger.debug(f"Sale {sale_id} has no children data (children is None or empty)")
        
        # Get Timer associated with this sale (if exists)
        timer_result = await db.execute(
            select(Timer).where(Timer.sale_id == sale_id)
        )
        timer = timer_result.scalar_one_or_none()
        
        if timer:
            logger.debug(f"Timer found for sale {sale_id}: child_name={timer.child_name}, child_age={timer.child_age}")
        else:
            logger.debug(f"No timer found for sale {sale_id}")
        
        # Get Sucursal for timezone
        sucursal_result = await db.execute(
            select(Sucursal).where(Sucursal.id == sale.sucursal_id)
        )
        sucursal = sucursal_result.scalar_one_or_none()
        
        # Get timezone string (default to America/Mexico_City if sucursal not found)
        timezone_str = sucursal.timezone if sucursal else "America/Mexico_City"
        
        # Get item names (services/products) for display
        # Also determine if this is a product or product package sale for ticket label
        item_names = {}
        is_product_sale = sale.tipo == "product"
        is_product_package_sale = False
        
        for item in sale.items:
            if item.type == "service":
                result = await db.execute(
                    select(Service).where(Service.id == item.ref_id)
                )
                service = result.scalar_one_or_none()
                item_names[str(item.ref_id)] = service.name if service else f"Servicio {str(item.ref_id)[:8]}"
            elif item.type == "product":
                result = await db.execute(
                    select(Product).where(Product.id == item.ref_id)
                )
                product = result.scalar_one_or_none()
                item_names[str(item.ref_id)] = product.name if product else f"Producto {str(item.ref_id)[:8]}"
            elif item.type == "package":
                # Check if this is a product package
                package_result = await db.execute(
                    select(Package).where(Package.id == item.ref_id)
                )
                package = package_result.scalar_one_or_none()
                if package:
                    from utils.package_helpers import is_product_package
                    if is_product_package(package):
                        is_product_package_sale = True
                    item_names[str(item.ref_id)] = package.name if package else f"Paquete {str(item.ref_id)[:8]}"
                else:
                    item_names[str(item.ref_id)] = f"Paquete {str(item.ref_id)[:8]}"
            else:
                item_names[str(item.ref_id)] = f"{item.type.title()} {str(item.ref_id)[:8]}"
        
        # Determine label for payer name field
        # Use "Nombre del cliente" for products and product packages
        # Use "Nombre del adulto responsable" for services and service packages
        payer_name_label = "Nombre del cliente" if (is_product_sale or is_product_package_sale) else "Nombre del adulto responsable"
        
        # Format payment method
        payment_method_labels = {
            "cash": "Efectivo",
            "card": "Tarjeta",
            "transfer": "Transferencia"
        }
        payment_label = payment_method_labels.get(sale.payment_method, sale.payment_method)
        
        # Format dates with timezone conversion
        created_date, _ = format_datetime_local(sale.created_at, timezone_str)
        
        # Format timer times (entry and exit) with timezone conversion
        # Hora de entrada = timer.entry_time (ya incluye el delay de 3 minutos después de la venta)
        # Esta es la hora real cuando el niño entra, que se imprime en el ticket
        entry_time_str = format_time_local(timer.entry_time, timezone_str) if timer and timer.entry_time else "N/A"
        
        # Hora de salida = cuando termina el timer (ya incluye el delay + duration)
        exit_time_str = format_time_local(timer.exit_time, timezone_str) if timer and timer.exit_time else "N/A"
        
        # Format prices
        def format_price(cents: int) -> str:
            return f"${cents / 100:.2f}"
        
        # Format scheduled date (handles both date and datetime objects)
        def format_scheduled_date(scheduled_date_obj, tz_str: str) -> str:
            """
            Format scheduled_date for ticket display.
            
            The scheduled_date is stored as UTC datetime representing midnight in the sucursal's timezone.
            This function converts it back to the sucursal's timezone and extracts only the date portion
            to avoid day shifts due to timezone conversion.
            
            Args:
                scheduled_date_obj: UTC datetime (timezone-aware) or date object
                tz_str: IANA timezone string (sucursal timezone)
                
            Returns:
                Formatted date string (DD/MM/YYYY) in the sucursal's timezone
            """
            if not scheduled_date_obj:
                return ""
            
            try:
                from datetime import date as dt_date
                
                # If it's a date object, it means it wasn't properly converted (edge case)
                # Convert it using the timezone context
                if isinstance(scheduled_date_obj, dt_date) and not isinstance(scheduled_date_obj, datetime):
                    # This shouldn't happen if create_local_midnight_datetime was used,
                    # but handle it gracefully
                    scheduled_datetime = create_local_midnight_datetime(scheduled_date_obj, tz_str)
                elif isinstance(scheduled_date_obj, datetime):
                    # It's already a datetime object (should be UTC timezone-aware)
                    scheduled_datetime = scheduled_date_obj
                    # Ensure it's timezone-aware (assume UTC if naive)
                    if scheduled_datetime.tzinfo is None:
                        scheduled_datetime = scheduled_datetime.replace(tzinfo=timezone.utc)
                else:
                    # Fallback: try to convert string or other types
                    logger.warning(f"Unexpected scheduled_date type: {type(scheduled_date_obj)}")
                    return str(scheduled_date_obj)
                
                # Convert from UTC to sucursal timezone and extract date only
                # This ensures the date displayed matches the date selected by the user
                date_str, _ = format_datetime_local(scheduled_datetime, tz_str, date_format="%d/%m/%Y")
                return date_str
            except (AttributeError, TypeError, ValueError) as e:
                logger.warning(f"Error formatting scheduled_date: {e}", exc_info=True)
                # Fallback: try to format as string
                return str(scheduled_date_obj)
        
        # Format children information for ticket
        def format_children_info(sale: Sale, timer: Optional[Timer], original_sale: Optional[Sale] = None) -> str:
            """
            Format children information for ticket display.
            Shows horizontal list of children: "Juan (5), María (7), Pedro (4)"
            Fallback cascade: sale.children → original_sale.children → timer.child_name/child_age
            """
            # Priority 1: use children array from sale if available
            if sale.children:
                try:
                    # JSONB from SQLAlchemy can be a list directly or need parsing
                    children_data = sale.children
                    if not isinstance(children_data, list):
                        # If it's not a list, try to parse it
                        if isinstance(children_data, str):
                            import json
                            children_data = json.loads(children_data)
                        else:
                            children_data = []
                    
                    if isinstance(children_data, list) and len(children_data) > 0:
                        children_list = []
                        for child in children_data:
                            # Handle both dict and object-like access
                            if isinstance(child, dict):
                                name = child.get("name", "") or ""
                                age = child.get("age")
                            else:
                                # Fallback for other types
                                name = getattr(child, "name", "") or ""
                                age = getattr(child, "age", None)
                            
                            if name:
                                if age:
                                    children_list.append(f"{name} ({age})")
                                else:
                                    children_list.append(name)
                        
                        if children_list:
                            children_text = ", ".join(children_list)
                            return f'<div class="info-row"><span class="info-label">Niños:</span><span class="children-list">{children_text}</span></div>'
                except (AttributeError, TypeError, ValueError) as e:
                    # Log error but don't break ticket generation
                    logger.warning(f"Error formatting children info from sale: {e}")
            
            # Priority 2: fallback to original_sale.children if available (for extension tickets)
            if original_sale and original_sale.children:
                try:
                    # JSONB from SQLAlchemy can be a list directly or need parsing
                    children_data = original_sale.children
                    if not isinstance(children_data, list):
                        # If it's not a list, try to parse it
                        if isinstance(children_data, str):
                            import json
                            children_data = json.loads(children_data)
                        else:
                            children_data = []
                    
                    if isinstance(children_data, list) and len(children_data) > 0:
                        children_list = []
                        for child in children_data:
                            # Handle both dict and object-like access
                            if isinstance(child, dict):
                                name = child.get("name", "") or ""
                                age = child.get("age")
                            else:
                                # Fallback for other types
                                name = getattr(child, "name", "") or ""
                                age = getattr(child, "age", None)
                            
                            if name:
                                if age:
                                    children_list.append(f"{name} ({age})")
                                else:
                                    children_list.append(name)
                        
                        if children_list:
                            children_text = ", ".join(children_list)
                            return f'<div class="info-row"><span class="info-label">Niños:</span><span class="children-list">{children_text}</span></div>'
                except (AttributeError, TypeError, ValueError) as e:
                    # Log error but don't break ticket generation
                    logger.warning(f"Error formatting children info from original_sale: {e}")
            
            # Priority 3: fallback to legacy single-child format from timer
            if timer and timer.child_name:
                age_text = f" ({timer.child_age})" if timer.child_age else ""
                return f'<div class="info-row"><span class="info-label">Nombre del niño:</span><span>{timer.child_name}{age_text}</span></div>'
            
            return ""
        
        # Generate HTML
        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ticket de Venta - KIDYLAND</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.4;
            padding: 20px;
            color: #000;
            background: #fff;
        }}
        
        @media print {{
            body {{
                padding: 10px;
            }}
            
            .no-print {{
                display: none;
            }}
        }}
        
        .ticket {{
            max-width: 300px;
            margin: 0 auto;
            border: 1px solid #000;
            padding: 15px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 15px;
            border-bottom: 2px solid #000;
            padding-bottom: 10px;
        }}
        
        .header h1 {{
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 2px;
            margin-bottom: 5px;
        }}
        
        .header p {{
            font-size: 10px;
        }}
        
        .sale-info {{
            margin-bottom: 15px;
        }}
        
        .info-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            font-size: 11px;
        }}
        
        .info-label {{
            font-weight: bold;
        }}
        
        .children-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            max-width: 200px;
        }}
        
        .items-section {{
            margin-bottom: 15px;
            border-top: 1px dashed #000;
            border-bottom: 1px dashed #000;
            padding: 10px 0;
        }}
        
        .item-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 11px;
        }}
        
        .item-name {{
            flex: 1;
            margin-right: 10px;
        }}
        
        .item-qty {{
            margin-right: 10px;
            min-width: 30px;
        }}
        
        .item-price {{
            text-align: right;
            min-width: 70px;
        }}
        
        .totals-section {{
            margin-bottom: 15px;
        }}
        
        .total-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            font-size: 12px;
        }}
        
        .total-row.grand-total {{
            font-size: 16px;
            font-weight: bold;
            border-top: 2px solid #000;
            border-bottom: 2px solid #000;
            padding: 8px 0;
            margin-top: 10px;
        }}
        
        .payment-section {{
            margin-bottom: 15px;
            padding-top: 10px;
            border-top: 1px dashed #000;
        }}
        
        .footer {{
            text-align: center;
            font-size: 10px;
            color: #666;
            margin-top: 15px;
            padding-top: 10px;
            border-top: 1px dashed #000;
        }}
    </style>
</head>
<body>
    <div class="ticket">
        <div class="header">
            <h1>KIDYLAND</h1>
            <p>Ticket de Venta</p>
        </div>
        
        <div class="sale-info">
            <div class="info-row">
                <span class="info-label">Ticket #:</span>
                <span>{str(sale.id)[:8].upper()}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Fecha:</span>
                <span>{created_date}</span>
            </div>
            {format_children_info(sale, timer)}
            {f'<div class="info-row"><span class="info-label">{payer_name_label}:</span><span>{sale.payer_name}</span></div>' if sale.payer_name else ''}
            {f'<div class="info-row"><span class="info-label">Teléfono:</span><span>{sale.payer_phone}</span></div>' if sale.payer_phone else ''}
            {f'<div class="info-row"><span class="info-label">Fecha Programada:</span><span>{format_scheduled_date(sale.scheduled_date, timezone_str)}</span></div>' if sale.scheduled_date else ''}
            {f'<div class="info-row"><span class="info-label">Hora de entrada:</span><span>{entry_time_str}</span></div>' if timer else ''}
            {f'<div class="info-row"><span class="info-label">Hora de salida:</span><span>{exit_time_str}</span></div>' if timer and timer.exit_time else ''}
        </div>
        
        <div class="items-section">
            <div class="info-row" style="margin-bottom: 10px; font-weight: bold;">
                <span>Descripción</span>
                <span>Cant.</span>
                <span>Total</span>
            </div>
            {''.join([
                f'<div class="item-row"><span class="item-name">{item_names.get(str(item.ref_id), "Item")}</span><span class="item-qty">{item.quantity}</span><span class="item-price">{format_price(item.subtotal_cents)}</span></div>'
                for item in sale.items
            ])}
        </div>
        
        <div class="totals-section">
            <div class="total-row">
                <span>Subtotal:</span>
                <span>{format_price(sale.subtotal_cents)}</span>
            </div>
            {f'<div class="total-row"><span>Descuento:</span><span>-{format_price(sale.discount_cents)}</span></div>' if sale.discount_cents > 0 else ''}
            <div class="total-row grand-total">
                <span>TOTAL:</span>
                <span>{format_price(sale.total_cents)}</span>
            </div>
        </div>
        
        <div class="payment-section">
            <div class="info-row">
                <span class="info-label">Método de Pago:</span>
                <span>{payment_label}</span>
            </div>
            {f'<div class="info-row"><span class="info-label">Efectivo Recibido:</span><span>{format_price(sale.cash_received_cents)}</span></div>' if sale.cash_received_cents else ''}
            {f'<div class="info-row"><span class="info-label">Código Autorización:</span><span>{sale.card_auth_code}</span></div>' if sale.card_auth_code else ''}
            {f'<div class="info-row"><span class="info-label">Referencia Transferencia:</span><span>{sale.transfer_reference}</span></div>' if sale.transfer_reference else ''}
            {f'<div class="info-row"><span class="info-label">Cambio:</span><span>{format_price(sale.cash_received_cents - sale.total_cents)}</span></div>' if sale.cash_received_cents and sale.cash_received_cents > sale.total_cents else ''}
        </div>
        
        <div class="footer">
            <p>¡Gracias por su compra!</p>
            <div style="margin-top: 15px; padding-top: 10px; border-top: 1px dashed #000; font-size: 9px; text-align: left;">
                <p style="margin-bottom: 10px;">Al firmar este ticket acepta nuestra política de uso con términos y condiciones</p>
                <div style="margin-top: 15px;">
                    <p style="margin-bottom: 5px;">Firma del adulto responsable:</p>
                    <div style="border-bottom: 1px solid #000; height: 30px; margin-top: 5px;"></div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""
        
        logger.info(f"Ticket HTML generated for sale {sale_id}")
        return html
    
    @staticmethod
    async def extend_timer_with_sale(
        db: AsyncSession,
        original_sale_id: UUID,
        duration_minutes: int,
        payment_method: str,
        payer_name: Optional[str] = None,
        payer_phone: Optional[str] = None,
        payer_signature: Optional[str] = None,
        cash_received_cents: Optional[int] = None,
        card_auth_code: Optional[str] = None,
        transfer_reference: Optional[str] = None,
        current_user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Extend a timer by creating a new sale with service extension.
        
        This method:
        1. Gets the original sale and its timer
        2. Validates the extension duration is valid for the service
        3. Calculates price from service.duration_prices
        4. Creates a new sale with the extension item
        5. Extends the timer
        6. Clears obsolete alerts for the extended timer
        7. Generates a ticket HTML with contextual message
        
        Args:
            db: Database session
            original_sale_id: ID of the original sale that has the timer
            duration_minutes: Duration to extend (must be in service.durations_allowed)
            payment_method: Payment method for the extension ("cash", "card", "transfer")
            payer_name: Optional payer name (defaults to original sale payer_name)
            payer_phone: Optional payer phone (defaults to original sale payer_phone)
            payer_signature: Optional payer signature (defaults to original sale payer_signature)
            cash_received_cents: Required if payment_method is "cash"
            card_auth_code: Required if payment_method is "card"
            transfer_reference: Required if payment_method is "transfer"
            current_user: Current authenticated user (optional, defaults to original sale user)
            
        Returns:
            Dictionary with:
            {
                "sale_id": str,  # New sale ID
                "timer_id": str,  # Extended timer ID
                "sale": dict,     # New sale data
                "timer": dict,    # Extended timer data
                "ticket_html": str  # HTML ticket for printing
            }
            
        Raises:
            ValueError: If sale/timer not found, invalid duration, or validation fails
        """
        # Get original sale with items
        original_sale = await SaleService.get_sale_with_items(db, original_sale_id)
        if not original_sale:
            raise ValueError(f"Original sale with ID {original_sale_id} not found")
        
        # Note: Day validation is handled by require_active_day dependency in the router.
        # This check serves as a fallback defense-in-depth measure.
        # The primary validation happens at the FastAPI dependency level before this code executes.
        active_day = await DayStartService.get_active_day(db, str(original_sale.sucursal_id))
        if not active_day:
            raise ValueError(
                "No se puede extender el timer. El día no ha sido iniciado. "
                "Por favor, inicie el día desde la sección de Reportes antes de realizar extensiones."
            )
        
        # Get timer associated with original sale
        timer_result = await db.execute(
            select(Timer).where(Timer.sale_id == original_sale_id)
        )
        timer = timer_result.scalar_one_or_none()
        if not timer:
            raise ValueError(f"No timer found for sale {original_sale_id}")
        
        if timer.status not in ["active", "extended"]:
            raise ValueError(f"Timer {timer.id} is not active or extended (status: {timer.status})")
        
        # Get service to validate duration and get price
        service_result = await db.execute(
            select(Service).where(Service.id == timer.service_id)
        )
        service = service_result.scalar_one_or_none()
        if not service:
            raise ValueError(f"Service {timer.service_id} not found")
        
        # Validate duration is in durations_allowed
        if duration_minutes not in (service.durations_allowed or []):
            raise ValueError(
                f"Duration {duration_minutes} minutes is not allowed for service {service.name}. "
                f"Allowed durations: {service.durations_allowed}"
            )
        
        # Get price from duration_prices (using normalized property for robust access)
        duration_prices = service.duration_prices_normalized
        if not duration_prices or duration_minutes not in duration_prices:
            raise ValueError(
                f"No price found for duration {duration_minutes} minutes in service {service.name}. "
                f"Available durations with prices: {list(duration_prices.keys()) if duration_prices else 'none'}"
            )
        unit_price_cents = duration_prices[duration_minutes]
        
        # Calculate quantity from original sale's children (for multi-child sales)
        # If original sale has children array, use its length; otherwise default to 1
        quantity = 1  # Default for backward compatibility
        if original_sale.children:
            try:
                # JSONB from SQLAlchemy can be a list directly
                children_data = original_sale.children
                if not isinstance(children_data, list):
                    # If it's not a list, try to parse it
                    if isinstance(children_data, str):
                        import json
                        children_data = json.loads(children_data)
                    else:
                        children_data = []
                
                if isinstance(children_data, list) and len(children_data) > 0:
                    quantity = len(children_data)
            except (AttributeError, TypeError, ValueError) as e:
                # Log warning but continue with quantity = 1 (backward compatibility)
                logger.warning(f"Error parsing children data for sale {original_sale_id}: {e}. Using quantity=1.")
        
        # Calculate subtotal: unit price × quantity (for multi-child extensions)
        subtotal_cents = unit_price_cents * quantity
        
        # Use original sale data as defaults
        final_payer_name = payer_name or original_sale.payer_name
        final_payer_phone = payer_phone or original_sale.payer_phone
        final_payer_signature = payer_signature or original_sale.payer_signature
        
        # Get user ID - use current_user if provided, otherwise use original sale's user
        if current_user:
            final_user_id = current_user.id
        else:
            # Get original sale's user
            final_user_id = original_sale.usuario_id
        
        # Calculate totals (no discount for extensions)
        total_cents = subtotal_cents
        
        # Validate payment method specific fields
        if payment_method == "cash":
            if cash_received_cents is None or cash_received_cents < total_cents:
                raise ValueError(f"cash_received_cents must be at least {total_cents} for cash payment")
        elif payment_method == "card":
            if not card_auth_code:
                raise ValueError("card_auth_code is required for card payment")
        elif payment_method == "transfer":
            if not transfer_reference:
                raise ValueError("transfer_reference is required for transfer payment")
        else:
            raise ValueError(f"Invalid payment_method: {payment_method}")
        
        # Create new sale for extension
        new_sale = Sale(
            sucursal_id=original_sale.sucursal_id,
            usuario_id=final_user_id,
            tipo="service",
            subtotal_cents=subtotal_cents,
            discount_cents=0,
            total_cents=total_cents,
            payer_name=final_payer_name,
            payer_phone=final_payer_phone,
            payer_signature=final_payer_signature,
            payment_method=payment_method,
            cash_received_cents=cash_received_cents or 0,
            card_auth_code=card_auth_code,
            transfer_reference=transfer_reference,
        )
        db.add(new_sale)
        await db.flush()
        
        # Create sale item for extension
        extension_item = SaleItem(
            sale_id=new_sale.id,
            type="service",
            ref_id=service.id,
            quantity=quantity,  # Use calculated quantity (for multi-child extensions)
            unit_price_cents=unit_price_cents,
            subtotal_cents=subtotal_cents,
        )
        db.add(extension_item)
        await db.flush()
        
        # Extend timer using TimerService
        from services.timer_service import TimerService
        extended_timer = await TimerService.extend_timer(
            db=db,
            timer_id=str(timer.id),
            minutes_to_add=duration_minutes
        )
        
        # Calculate new time_left_minutes after extension
        # This calculation must be consistent with TimerService.get_timers_with_time_left()
        # to ensure the frontend receives accurate time_left immediately after extension
        now = datetime.now(timezone.utc)
        new_time_left_minutes = 0
        if extended_timer.end_at:
            end_at = extended_timer.end_at
            # Normalize to UTC (consistent with get_timers_with_time_left logic)
            if end_at.tzinfo is None:
                end_at = end_at.replace(tzinfo=timezone.utc)
            else:
                end_at = end_at.astimezone(timezone.utc)
            delta = end_at - now
            new_time_left_minutes = max(0, int(delta.total_seconds() / 60))
        
        # Clear obsolete alerts for extended timer
        TimerAlertService.clear_obsolete_alerts_for_timer(
            timer_id=str(timer.id),
            new_time_left_minutes=new_time_left_minutes
        )
        
        # Commit all changes
        await db.commit()
        await db.refresh(new_sale)
        await db.refresh(extended_timer)
        
        # Generate ticket HTML with extension context
        ticket_html = await SaleService.generate_ticket_html_with_extension_context(
            db=db,
            sale_id=new_sale.id,
            original_sale_id=original_sale_id,
            extension_duration_minutes=duration_minutes
        )
        
        # Serialize response
        sale_dict = {
            "id": str(new_sale.id),
            "sucursal_id": str(new_sale.sucursal_id),
            "usuario_id": str(new_sale.usuario_id),
            "tipo": new_sale.tipo,
            "subtotal_cents": new_sale.subtotal_cents,
            "discount_cents": new_sale.discount_cents,
            "total_cents": new_sale.total_cents,
            "payer_name": new_sale.payer_name,
            "payer_phone": new_sale.payer_phone,
            "payer_signature": new_sale.payer_signature,
            "payment_method": new_sale.payment_method,
            "cash_received_cents": new_sale.cash_received_cents,
            "card_auth_code": new_sale.card_auth_code,
            "transfer_reference": new_sale.transfer_reference,
            "created_at": new_sale.created_at.isoformat() if new_sale.created_at else None,
            "updated_at": new_sale.updated_at.isoformat() if new_sale.updated_at else None,
        }
        
        # Include time_left_minutes in timer_dict for immediate frontend update
        # This eliminates the perceived delay until WebSocket update (every 5 seconds)
        timer_dict = {
            "id": str(extended_timer.id),
            "sale_id": str(extended_timer.sale_id),
            "service_id": str(extended_timer.service_id),
            "start_delay_minutes": extended_timer.start_delay_minutes,
            "child_name": extended_timer.child_name,
            "child_age": extended_timer.child_age,
            "status": extended_timer.status,
            "start_at": extended_timer.start_at.isoformat() if extended_timer.start_at else None,
            "end_at": extended_timer.end_at.isoformat() if extended_timer.end_at else None,
            "entry_time": extended_timer.entry_time.isoformat() if extended_timer.entry_time else None,
            "exit_time": extended_timer.exit_time.isoformat() if extended_timer.exit_time else None,
            "created_at": extended_timer.created_at.isoformat() if extended_timer.created_at else None,
            "updated_at": extended_timer.updated_at.isoformat() if extended_timer.updated_at else None,
            "time_left_minutes": new_time_left_minutes,  # Include calculated time_left for immediate UI update
        }
        
        logger.info(
            f"Timer extended with sale: timer_id={timer.id}, new_sale_id={new_sale.id}, "
            f"duration_minutes={duration_minutes}, new_time_left={new_time_left_minutes}"
        )
        
        return {
            "sale_id": str(new_sale.id),
            "timer_id": str(extended_timer.id),
            "sale": sale_dict,
            "timer": timer_dict,
            "ticket_html": ticket_html,
        }
    
    @staticmethod
    async def generate_ticket_html_with_extension_context(
        db: AsyncSession,
        sale_id: UUID,
        original_sale_id: UUID,
        extension_duration_minutes: int
    ) -> str:
        """
        Generate ticket HTML for an extension sale with contextual message.
        
        Args:
            db: Database session
            sale_id: ID of the extension sale
            original_sale_id: ID of the original sale
            extension_duration_minutes: Duration of the extension
            
        Returns:
            HTML string for the ticket with extension context
        """
        # Get extension sale with items
        sale = await SaleService.get_sale_with_items(db, sale_id)
        if not sale:
            raise ValueError(f"Sale with ID {sale_id} not found")
        
        # Get original sale with items (for fallback to original_sale.children if extension sale doesn't have children)
        original_sale = await SaleService.get_sale_with_items(db, original_sale_id)
        if not original_sale:
            logger.warning(f"Original sale with ID {original_sale_id} not found, continuing without original_sale fallback")
            original_sale = None
        
        # Get Timer associated with the original sale
        timer_result = await db.execute(
            select(Timer).where(Timer.sale_id == original_sale_id)
        )
        timer = timer_result.scalar_one_or_none()
        
        # Get Sucursal for timezone
        sucursal_result = await db.execute(
            select(Sucursal).where(Sucursal.id == sale.sucursal_id)
        )
        sucursal = sucursal_result.scalar_one_or_none()
        timezone_str = sucursal.timezone if sucursal else "America/Mexico_City"
        
        # Get item names
        # Also determine if this is a product or product package sale for ticket label
        item_names = {}
        is_product_sale = sale.tipo == "product"
        is_product_package_sale = False
        
        for item in sale.items:
            if item.type == "service":
                result = await db.execute(
                    select(Service).where(Service.id == item.ref_id)
                )
                service = result.scalar_one_or_none()
                item_names[str(item.ref_id)] = service.name if service else f"Servicio {str(item.ref_id)[:8]}"
            elif item.type == "product":
                result = await db.execute(
                    select(Product).where(Product.id == item.ref_id)
                )
                product = result.scalar_one_or_none()
                item_names[str(item.ref_id)] = product.name if product else f"Producto {str(item.ref_id)[:8]}"
            elif item.type == "package":
                # Check if this is a product package
                package_result = await db.execute(
                    select(Package).where(Package.id == item.ref_id)
                )
                package = package_result.scalar_one_or_none()
                if package:
                    from utils.package_helpers import is_product_package
                    if is_product_package(package):
                        is_product_package_sale = True
                    item_names[str(item.ref_id)] = package.name if package else f"Paquete {str(item.ref_id)[:8]}"
                else:
                    item_names[str(item.ref_id)] = f"Paquete {str(item.ref_id)[:8]}"
            else:
                item_names[str(item.ref_id)] = f"{item.type.title()} {str(item.ref_id)[:8]}"
        
        # Determine label for payer name field
        # Use "Nombre del cliente" for products and product packages
        # Use "Nombre del adulto responsable" for services and service packages
        payer_name_label = "Nombre del cliente" if (is_product_sale or is_product_package_sale) else "Nombre del adulto responsable"
        
        # Format payment method
        payment_method_labels = {
            "cash": "Efectivo",
            "card": "Tarjeta",
            "transfer": "Transferencia"
        }
        payment_label = payment_method_labels.get(sale.payment_method, sale.payment_method)
        
        # Format dates
        created_date, _ = format_datetime_local(sale.created_at, timezone_str)
        
        # Format timer times
        entry_time_str = format_time_local(timer.entry_time, timezone_str) if timer and timer.entry_time else "N/A"
        exit_time_str = format_time_local(timer.exit_time, timezone_str) if timer and timer.exit_time else "N/A"
        
        # Format prices
        def format_price(cents: int) -> str:
            return f"${cents / 100:.2f}"
        
        # Format duration
        def format_duration(minutes: int) -> str:
            if minutes < 60:
                return f"{minutes} minutos"
            hours = minutes // 60
            mins = minutes % 60
            if mins == 0:
                return f"{hours} {'hora' if hours == 1 else 'horas'}"
            return f"{hours}h {mins}min"
        
        # Format scheduled date (handles both date and datetime objects)
        def format_scheduled_date(scheduled_date_obj, tz_str: str) -> str:
            """
            Format scheduled_date for ticket display.
            
            The scheduled_date is stored as UTC datetime representing midnight in the sucursal's timezone.
            This function converts it back to the sucursal's timezone and extracts only the date portion
            to avoid day shifts due to timezone conversion.
            
            Args:
                scheduled_date_obj: UTC datetime (timezone-aware) or date object
                tz_str: IANA timezone string (sucursal timezone)
                
            Returns:
                Formatted date string (DD/MM/YYYY) in the sucursal's timezone
            """
            if not scheduled_date_obj:
                return ""
            
            try:
                from datetime import date as dt_date
                
                # If it's a date object, it means it wasn't properly converted (edge case)
                # Convert it using the timezone context
                if isinstance(scheduled_date_obj, dt_date) and not isinstance(scheduled_date_obj, datetime):
                    # This shouldn't happen if create_local_midnight_datetime was used,
                    # but handle it gracefully
                    scheduled_datetime = create_local_midnight_datetime(scheduled_date_obj, tz_str)
                elif isinstance(scheduled_date_obj, datetime):
                    # It's already a datetime object (should be UTC timezone-aware)
                    scheduled_datetime = scheduled_date_obj
                    # Ensure it's timezone-aware (assume UTC if naive)
                    if scheduled_datetime.tzinfo is None:
                        scheduled_datetime = scheduled_datetime.replace(tzinfo=timezone.utc)
                else:
                    # Fallback: try to convert string or other types
                    logger.warning(f"Unexpected scheduled_date type: {type(scheduled_date_obj)}")
                    return str(scheduled_date_obj)
                
                # Convert from UTC to sucursal timezone and extract date only
                # This ensures the date displayed matches the date selected by the user
                date_str, _ = format_datetime_local(scheduled_datetime, tz_str, date_format="%d/%m/%Y")
                return date_str
            except (AttributeError, TypeError, ValueError) as e:
                logger.warning(f"Error formatting scheduled_date: {e}", exc_info=True)
                # Fallback: try to format as string
                return str(scheduled_date_obj)
        
        # Format children information for ticket
        def format_children_info(sale: Sale, timer: Optional[Timer], original_sale: Optional[Sale] = None) -> str:
            """
            Format children information for ticket display.
            Shows horizontal list of children: "Juan (5), María (7), Pedro (4)"
            Fallback cascade: sale.children → original_sale.children → timer.child_name/child_age
            """
            # Priority 1: use children array from extension sale if available
            if sale.children:
                try:
                    # JSONB from SQLAlchemy can be a list directly or need parsing
                    children_data = sale.children
                    if not isinstance(children_data, list):
                        # If it's not a list, try to parse it
                        if isinstance(children_data, str):
                            import json
                            children_data = json.loads(children_data)
                        else:
                            children_data = []
                    
                    if isinstance(children_data, list) and len(children_data) > 0:
                        children_list = []
                        for child in children_data:
                            # Handle both dict and object-like access
                            if isinstance(child, dict):
                                name = child.get("name", "") or ""
                                age = child.get("age")
                            else:
                                # Fallback for other types
                                name = getattr(child, "name", "") or ""
                                age = getattr(child, "age", None)
                            
                            if name:
                                if age:
                                    children_list.append(f"{name} ({age})")
                                else:
                                    children_list.append(name)
                        
                        if children_list:
                            children_text = ", ".join(children_list)
                            return f'<div class="info-row"><span class="info-label">Niños:</span><span class="children-list">{children_text}</span></div>'
                except (AttributeError, TypeError, ValueError) as e:
                    # Log error but don't break ticket generation
                    logger.warning(f"Error formatting children info from sale: {e}")
            
            # Priority 2: fallback to original_sale.children if available (for extension tickets)
            if original_sale and original_sale.children:
                try:
                    # JSONB from SQLAlchemy can be a list directly or need parsing
                    children_data = original_sale.children
                    if not isinstance(children_data, list):
                        # If it's not a list, try to parse it
                        if isinstance(children_data, str):
                            import json
                            children_data = json.loads(children_data)
                        else:
                            children_data = []
                    
                    if isinstance(children_data, list) and len(children_data) > 0:
                        children_list = []
                        for child in children_data:
                            # Handle both dict and object-like access
                            if isinstance(child, dict):
                                name = child.get("name", "") or ""
                                age = child.get("age")
                            else:
                                # Fallback for other types
                                name = getattr(child, "name", "") or ""
                                age = getattr(child, "age", None)
                            
                            if name:
                                if age:
                                    children_list.append(f"{name} ({age})")
                                else:
                                    children_list.append(name)
                        
                        if children_list:
                            children_text = ", ".join(children_list)
                            return f'<div class="info-row"><span class="info-label">Niños:</span><span class="children-list">{children_text}</span></div>'
                except (AttributeError, TypeError, ValueError) as e:
                    # Log error but don't break ticket generation
                    logger.warning(f"Error formatting children info from original_sale: {e}")
            
            # Priority 3: fallback to legacy single-child format from timer
            if timer and timer.child_name:
                age_text = f" ({timer.child_age})" if timer.child_age else ""
                return f'<div class="info-row"><span class="info-label">Nombre del niño:</span><span>{timer.child_name}{age_text}</span></div>'
            
            return ""
        
        # Generate HTML with extension context
        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ticket de Extensión - KIDYLAND</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.4;
            padding: 20px;
            color: #000;
            background: #fff;
        }}
        
        @media print {{
            body {{
                padding: 10px;
            }}
            
            .no-print {{
                display: none;
            }}
        }}
        
        .ticket {{
            max-width: 300px;
            margin: 0 auto;
            border: 1px solid #000;
            padding: 15px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 15px;
            border-bottom: 2px solid #000;
            padding-bottom: 10px;
        }}
        
        .header h1 {{
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 2px;
            margin-bottom: 5px;
        }}
        
        .header p {{
            font-size: 10px;
        }}
        
        .extension-notice {{
            background-color: #fff;
            border: 2px dashed #000;
            padding: 10px;
            margin-bottom: 15px;
            text-align: center;
            font-weight: bold;
            font-size: 11px;
        }}
        
        .sale-info {{
            margin-bottom: 15px;
        }}
        
        .info-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            font-size: 11px;
        }}
        
        .info-label {{
            font-weight: bold;
        }}
        
        .children-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            max-width: 200px;
        }}
        
        .items-section {{
            margin-bottom: 15px;
            border-top: 1px dashed #000;
            border-bottom: 1px dashed #000;
            padding: 10px 0;
        }}
        
        .item-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 11px;
        }}
        
        .item-name {{
            flex: 1;
            margin-right: 10px;
        }}
        
        .item-qty {{
            margin-right: 10px;
            min-width: 30px;
        }}
        
        .item-price {{
            text-align: right;
            min-width: 70px;
        }}
        
        .totals-section {{
            margin-bottom: 15px;
        }}
        
        .total-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            font-size: 12px;
        }}
        
        .total-row.grand-total {{
            font-size: 16px;
            font-weight: bold;
            border-top: 2px solid #000;
            border-bottom: 2px solid #000;
            padding: 8px 0;
            margin-top: 10px;
        }}
        
        .payment-section {{
            margin-bottom: 15px;
            padding-top: 10px;
            border-top: 1px dashed #000;
        }}
        
        .footer {{
            text-align: center;
            font-size: 10px;
            color: #666;
            margin-top: 15px;
            padding-top: 10px;
            border-top: 1px dashed #000;
        }}
    </style>
</head>
<body>
    <div class="ticket">
        <div class="header">
            <h1>KIDYLAND</h1>
            <p>Ticket de Extensión de Tiempo</p>
        </div>
        
        <div class="extension-notice">
            Extensión de {format_duration(extension_duration_minutes)}
        </div>
        
        <div class="sale-info">
            <div class="info-row">
                <span class="info-label">Ticket #:</span>
                <span>{str(sale.id)[:8].upper()}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Fecha:</span>
                <span>{created_date}</span>
            </div>
            {f'<div class="info-row"><span class="info-label">Ticket Original #:</span><span>{str(original_sale_id)[:8].upper()}</span></div>'}
            {format_children_info(sale, timer, original_sale)}
            {f'<div class="info-row"><span class="info-label">{payer_name_label}:</span><span>{sale.payer_name}</span></div>' if sale.payer_name else ''}
            {f'<div class="info-row"><span class="info-label">Teléfono:</span><span>{sale.payer_phone}</span></div>' if sale.payer_phone else ''}
            {f'<div class="info-row"><span class="info-label">Fecha Programada:</span><span>{format_scheduled_date(sale.scheduled_date, timezone_str)}</span></div>' if sale.scheduled_date else ''}
            {f'<div class="info-row"><span class="info-label">Hora de entrada:</span><span>{entry_time_str}</span></div>' if timer else ''}
            {f'<div class="info-row"><span class="info-label">Nueva hora de salida:</span><span>{exit_time_str}</span></div>' if timer and timer.exit_time else ''}
        </div>
        
        <div class="items-section">
            <div class="info-row" style="margin-bottom: 10px; font-weight: bold;">
                <span>Descripción</span>
                <span>Cant.</span>
                <span>Total</span>
            </div>
            {''.join([
                f'<div class="item-row"><span class="item-name">{item_names.get(str(item.ref_id), "Item")} - Extensión {format_duration(extension_duration_minutes)}</span><span class="item-qty">{item.quantity}</span><span class="item-price">{format_price(item.subtotal_cents)}</span></div>'
                for item in sale.items
            ])}
        </div>
        
        <div class="totals-section">
            <div class="total-row">
                <span>Subtotal:</span>
                <span>{format_price(sale.subtotal_cents)}</span>
            </div>
            {f'<div class="total-row"><span>Descuento:</span><span>-{format_price(sale.discount_cents)}</span></div>' if sale.discount_cents > 0 else ''}
            <div class="total-row grand-total">
                <span>TOTAL:</span>
                <span>{format_price(sale.total_cents)}</span>
            </div>
        </div>
        
        <div class="payment-section">
            <div class="info-row">
                <span class="info-label">Método de Pago:</span>
                <span>{payment_label}</span>
            </div>
            {f'<div class="info-row"><span class="info-label">Efectivo Recibido:</span><span>{format_price(sale.cash_received_cents)}</span></div>' if sale.cash_received_cents else ''}
            {f'<div class="info-row"><span class="info-label">Código Autorización:</span><span>{sale.card_auth_code}</span></div>' if sale.card_auth_code else ''}
            {f'<div class="info-row"><span class="info-label">Referencia Transferencia:</span><span>{sale.transfer_reference}</span></div>' if sale.transfer_reference else ''}
            {f'<div class="info-row"><span class="info-label">Cambio:</span><span>{format_price(sale.cash_received_cents - sale.total_cents)}</span></div>' if sale.cash_received_cents and sale.cash_received_cents > sale.total_cents else ''}
        </div>
        
        <div class="footer">
            <p>¡Gracias por su compra!</p>
            <div style="margin-top: 15px; padding-top: 10px; border-top: 1px dashed #000; font-size: 9px; text-align: left;">
                <p style="margin-bottom: 10px;">Al firmar este ticket acepta nuestra política de uso con términos y condiciones</p>
                <div style="margin-top: 15px;">
                    <p style="margin-bottom: 5px;">Firma del adulto responsable:</p>
                    <div style="border-bottom: 1px solid #000; height: 30px; margin-top: 5px;"></div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""
        
        logger.info(f"Extension ticket HTML generated for sale {sale_id}")
        return html
