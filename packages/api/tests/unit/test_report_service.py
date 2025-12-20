"""
Unit tests for ReportService.
"""
import pytest
from datetime import date, timedelta
from services.report_service import ReportService
from services.analytics_cache import AnalyticsCache


@pytest.mark.asyncio
@pytest.mark.unit
async def test_report_service_initialization():
    """Test that ReportService initializes with cache."""
    service = ReportService()
    assert service.cache is not None
    assert isinstance(service.cache, AnalyticsCache)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_report_service_cache_integration(test_db, test_sucursal):
    """Test that ReportService uses cache correctly."""
    service = ReportService()
    
    # First call should hit database
    report1 = await service.get_sales_report(
        db=test_db,
        sucursal_id=str(test_sucursal.id),
        use_cache=True
    )
    
    # Second call should hit cache
    report2 = await service.get_sales_report(
        db=test_db,
        sucursal_id=str(test_sucursal.id),
        use_cache=True
    )
    
    # Results should be the same
    assert report1 == report2
    
    # Verify cache was used (check stats)
    stats = await service.cache.get_stats()
    assert stats["total_entries"] > 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_report_service_no_cache(test_db, test_sucursal):
    """Test that ReportService can bypass cache."""
    service = ReportService()
    
    # Call with use_cache=False
    report = await service.get_sales_report(
        db=test_db,
        sucursal_id=str(test_sucursal.id),
        use_cache=False
    )
    
    # Should still return report
    assert report is not None
    assert "total_revenue_cents" in report


@pytest.mark.asyncio
@pytest.mark.unit
async def test_report_service_parallel_execution(test_db, test_sucursal):
    """Test that get_dashboard_summary executes in parallel."""
    import asyncio
    service = ReportService()
    
    start_time = asyncio.get_event_loop().time()
    
    summary = await service.get_dashboard_summary(
        db=test_db,
        sucursal_id=str(test_sucursal.id),
        use_cache=False
    )
    
    elapsed = asyncio.get_event_loop().time() - start_time
    
    # Should have all metrics
    assert "sales" in summary
    assert "stock" in summary
    assert "services" in summary
    assert "generated_at" in summary
    
    # Should complete reasonably fast (parallel execution)
    assert elapsed < 5.0  # Should be fast with parallel execution


