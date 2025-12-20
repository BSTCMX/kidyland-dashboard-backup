"""
Unit tests for PredictionService.
"""
import pytest
from datetime import date, timedelta
from services.prediction_service import PredictionService


@pytest.mark.asyncio
@pytest.mark.unit
async def test_prediction_service_initialization():
    """Test that PredictionService initializes correctly."""
    service = PredictionService()
    assert service.report_service is not None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_predict_sales_insufficient_data(test_db, test_sucursal):
    """Test sales prediction with insufficient data."""
    service = PredictionService()
    
    # With no sales data, should return insufficient_data
    prediction = await service.predict_sales(
        db=test_db,
        sucursal_id=str(test_sucursal.id),
        forecast_days=7
    )
    
    assert prediction["confidence"] == "low"
    assert "message" in prediction
    assert "insufficient_data" in prediction["method"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_predict_capacity_insufficient_data(test_db, test_sucursal):
    """Test capacity prediction with insufficient data."""
    service = PredictionService()
    
    # With no timer data, should return insufficient_data
    prediction = await service.predict_capacity(
        db=test_db,
        sucursal_id=str(test_sucursal.id),
        forecast_days=7
    )
    
    assert prediction["confidence"] == "low"
    assert "message" in prediction


@pytest.mark.asyncio
@pytest.mark.unit
async def test_predict_stock_needs_no_products(test_db):
    """Test stock prediction with no products."""
    service = PredictionService()
    
    prediction = await service.predict_stock_needs(
        db=test_db,
        forecast_days=7
    )
    
    assert prediction["confidence"] == "low"
    assert len(prediction["reorder_suggestions"]) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_generate_all_predictions_parallel(test_db, test_sucursal):
    """Test that generate_all_predictions executes in parallel."""
    import asyncio
    service = PredictionService()
    
    start_time = asyncio.get_event_loop().time()
    
    predictions = await service.generate_all_predictions(
        db=test_db,
        sucursal_id=str(test_sucursal.id),
        forecast_days=7
    )
    
    elapsed = asyncio.get_event_loop().time() - start_time
    
    # Should have all prediction types
    assert "sales" in predictions
    assert "capacity" in predictions
    assert "stock" in predictions
    assert "generated_at" in predictions
    assert "forecast_days" in predictions
    
    # Should complete reasonably fast (parallel execution)
    assert elapsed < 5.0


