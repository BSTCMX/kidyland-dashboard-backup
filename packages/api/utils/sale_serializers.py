"""
Sale serializers - Transform Sale models to frontend-compatible format.

Clean Architecture:
- Separates serialization logic from services and routers
- Transforms database models to match frontend TypeScript interfaces
"""
from typing import Dict, Any, List
from datetime import datetime

from models.sale import Sale
from models.sale_item import SaleItem


def serialize_sale_for_frontend(sale: Sale) -> Dict[str, Any]:
    """
    Serialize a Sale model to match frontend Sale type structure.
    
    Frontend expects:
    {
      id: string;
      sucursal_id: string;
      usuario_id: string;
      tipo: string;
      items: SaleItem[];
      pricing: { subtotal_cents, discount_cents, total_cents };
      payer: { name, phone, signature };
      payment: { method, cash_received_cents, card_auth_code };
      timestamps: { created_at, updated_at };
    }
    
    Args:
        sale: Sale model instance with items loaded
        
    Returns:
        Dictionary matching frontend Sale interface
    """
    # Serialize items - handle case where items might not be loaded or is None
    items: List[Dict[str, Any]] = []
    if sale.items is not None:
        for item in sale.items:
            item_dict: Dict[str, Any] = {
                "quantity": item.quantity,
                "unit_price_cents": item.unit_price_cents,
                "total_price_cents": item.subtotal_cents,  # subtotal_cents is the total for the item
            }
            
            # Map ref_id to appropriate field based on item type
            if item.type == "product":
                item_dict["product_id"] = str(item.ref_id)
            elif item.type == "service":
                item_dict["service_id"] = str(item.ref_id)
            elif item.type == "package":
                item_dict["package_id"] = str(item.ref_id)
            
            items.append(item_dict)
    
    # Determine payment method (handle "transfer" as "mixed" if needed, but frontend expects "cash" | "card" | "mixed")
    payment_method = sale.payment_method or "cash"  # Default to cash if None
    
    # Serialize children array - always return an array, even if empty
    # This ensures consistency: children is always an array (never None)
    # If sale.children is NULL in DB, return empty array []
    # If sale.children is [], return empty array []
    # If sale.children is [{"name": "...", "age": ...}], return as is
    children = []
    if sale.children:
        # Ensure it's always a list
        if isinstance(sale.children, list):
            children = sale.children
        else:
            # Handle edge case where it might be stored differently
            # Wrap single object in a list if needed
            children = [sale.children] if sale.children else []
    
    # Handle None values safely
    # Format scheduled_date if it exists (for package sales scheduled for future dates)
    scheduled_date_str = None
    if sale.scheduled_date:
        # scheduled_date is a datetime, format it as ISO date string (YYYY-MM-DD)
        scheduled_date_str = sale.scheduled_date.isoformat() if hasattr(sale.scheduled_date, 'isoformat') else str(sale.scheduled_date)
        # If it's a datetime, extract just the date part
        if 'T' in scheduled_date_str or ' ' in scheduled_date_str:
            scheduled_date_str = scheduled_date_str.split('T')[0].split(' ')[0]
    
    return {
        "id": str(sale.id),
        "sucursal_id": str(sale.sucursal_id),
        "usuario_id": str(sale.usuario_id),
        "tipo": sale.tipo or "",
        "items": items,
        "pricing": {
            "subtotal_cents": sale.subtotal_cents or 0,
            "discount_cents": sale.discount_cents or 0,
            "total_cents": sale.total_cents or 0,
        },
        "payer": {
            "name": sale.payer_name or "",
            "phone": sale.payer_phone or "",
            "signature": sale.payer_signature or "",
        },
        "payment": {
            "method": payment_method,
            "cash_received_cents": sale.cash_received_cents,
            "card_auth_code": sale.card_auth_code or "",
        },
        "children": children,  # Array of {name: string, age: number | null}
        "scheduled_date": scheduled_date_str,  # Scheduled date for package sales (YYYY-MM-DD format or None)
        "timestamps": {
            "created_at": sale.created_at.isoformat() if sale.created_at else "",
            "updated_at": sale.updated_at.isoformat() if sale.updated_at else None,
        },
    }


def serialize_sales_for_frontend(sales: List[Sale]) -> List[Dict[str, Any]]:
    """
    Serialize a list of Sale models to frontend format.
    
    Args:
        sales: List of Sale model instances with items loaded
        
    Returns:
        List of dictionaries matching frontend Sale interface
    """
    return [serialize_sale_for_frontend(sale) for sale in sales]





