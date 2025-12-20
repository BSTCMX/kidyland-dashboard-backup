"""
Export endpoints for generating Excel and PDF reports.

Security Rules:
- GET /exports/excel: super_admin and admin_viewer can export
- GET /exports/pdf: super_admin and admin_viewer can export
"""
import logging
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models.user import User
from services.export_service import ExportService
from utils.auth import get_current_user, require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/excel")
async def export_excel(
    sucursal_id: Optional[str] = Query(None, description="Optional: Filter by sucursal ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    report_type: str = Query("dashboard", description="Type of report"),
    sections: Optional[str] = Query(None, description="Comma-separated list of sections"),
    include_predictions: bool = Query(False, description="Include predictions if available"),
    module: Optional[str] = Query(None, description="Module filter (recepcion, kidibar, all)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role_check = Depends(require_role(["super_admin", "admin_viewer"])),
):
    """
    Export report as Excel file.
    
    Security: super_admin and admin_viewer can export.
    
    Args:
        sucursal_id: Optional sucursal ID to filter by
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        report_type: Type of report
        sections: Optional comma-separated list of sections
        include_predictions: Whether to include predictions
        module: Optional module filter
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        StreamingResponse with Excel file
    """
    export_service = ExportService()
    
    # Parse dates
    parsed_start_date = None
    parsed_end_date = None
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD"
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD"
            )
    
    # Parse sections
    sections_list = None
    if sections:
        sections_list = [s.strip() for s in sections.split(",")]
    
    # Generate Excel
    excel_buffer = await export_service.generate_excel_report(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        report_type=report_type,
        sections=sections_list,
        include_predictions=include_predictions,
        module=module,
    )
    
    filename = f"report_{report_type}_{date.today().isoformat()}.xlsx"
    
    return StreamingResponse(
        excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/pdf")
async def export_pdf(
    sucursal_id: Optional[str] = Query(None, description="Optional: Filter by sucursal ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    report_type: str = Query("dashboard", description="Type of report"),
    sections: Optional[str] = Query(None, description="Comma-separated list of sections"),
    include_predictions: bool = Query(False, description="Include predictions if available"),
    module: Optional[str] = Query(None, description="Module filter (recepcion, kidibar, all)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role_check = Depends(require_role(["super_admin", "admin_viewer"])),
):
    """
    Export report as PDF file.
    
    Security: super_admin and admin_viewer can export.
    
    Args:
        sucursal_id: Optional sucursal ID to filter by
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        report_type: Type of report
        sections: Optional comma-separated list of sections
        include_predictions: Whether to include predictions
        module: Optional module filter
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        StreamingResponse with PDF file
    """
    export_service = ExportService()
    
    # Parse dates
    parsed_start_date = None
    parsed_end_date = None
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD"
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD"
            )
    
    # Parse sections
    sections_list = None
    if sections:
        sections_list = [s.strip() for s in sections.split(",")]
    
    # Generate PDF
    pdf_buffer = await export_service.generate_pdf_report(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        report_type=report_type,
        sections=sections_list,
        include_predictions=include_predictions,
        module=module,
    )
    
    filename = f"report_{report_type}_{date.today().isoformat()}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
