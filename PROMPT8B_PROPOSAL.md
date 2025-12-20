# 🎯 PROMPT 8B - Business Logic + Analytics Essentials

**Objetivo:** Completar business logic crítico + Dashboard de métricas esenciales

---

## 📋 PARTE A: Completar Business Logic Crítico

### 1. **Routers/Users.py - CRUD Completo**
- ✅ Implementar `create_user` (solo super_admin)
- ✅ Implementar `list_users` (super_admin, admin_viewer)
- ✅ Implementar `get_user` (super_admin, admin_viewer)
- ✅ Implementar `update_user` (solo super_admin)
- ✅ Implementar `delete_user` (solo super_admin)

### 2. **App Admin Completa**
- ✅ Panel Super Admin con CRUD de usuarios
- ✅ Vista de todas las sucursales
- ✅ Gestión de roles y permisos

### 3. **Flujos de Venta Frontend**
- ✅ Reception: Formulario completo de venta
- ✅ KidiBar: Ventas rápidas de productos
- ✅ Integración con timers automáticos

---

## 📊 PARTE B: Analytics & Dashboard Essentials

### 1. **Endpoints de Reportes** (`/reports/*`)

#### `GET /reports/sales`
```python
Query params:
  - sucursal_id (optional)
  - start_date (optional)
  - end_date (optional)
  - period: "day" | "week" | "month" (default: "day")

Response:
{
  "total_revenue_cents": 150000,
  "average_transaction_value_cents": 5000,
  "sales_count": 30,
  "revenue_by_type": {
    "product": 50000,
    "service": 80000,
    "package": 20000
  },
  "revenue_by_payment_method": {
    "cash": 100000,
    "card": 50000
  },
  "period": "2025-12-02"
}
```

#### `GET /reports/stock`
```python
Query params:
  - sucursal_id (optional)
  - alert_only: bool (default: false)

Response:
{
  "low_stock_alerts": [
    {
      "product_id": "...",
      "name": "Product Name",
      "stock_qty": 3,
      "threshold_alert_qty": 5
    }
  ],
  "stock_turnover": [
    {
      "product_id": "...",
      "name": "Product Name",
      "sales_count": 50,
      "stock_turnover_rate": 2.5
    }
  ],
  "fast_movers": [...],
  "slow_movers": [...]
}
```

#### `GET /reports/services`
```python
Query params:
  - sucursal_id (optional)
  - service_id (optional)

Response:
{
  "active_timers_count": 5,
  "total_usage_hours": 12.5,
  "average_duration_minutes": 60,
  "utilization_rate": 75.0,  // Si tenemos capacity
  "service_breakdown": [
    {
      "service_id": "...",
      "name": "Service Name",
      "active_timers": 2,
      "total_hours": 4.5
    }
  ]
}
```

#### `GET /reports/dashboard`
```python
Response:
{
  "sales": {
    "today_revenue_cents": 50000,
    "today_sales_count": 10,
    "average_transaction_value_cents": 5000
  },
  "stock": {
    "low_stock_count": 3,
    "critical_alerts": 1
  },
  "services": {
    "active_timers": 5,
    "total_usage_hours": 12.5
  },
  "operations": {
    "day_close_pending": false,
    "last_day_close": "2025-12-01"
  }
}
```

### 2. **Service Model Enhancement** (Fase 2)

```python
# Agregar a Service model:
max_capacity = Column(Integer, nullable=True)  # Capacidad máxima simultánea
operating_hours_start = Column(Time, nullable=True)
operating_hours_end = Column(Time, nullable=True)
```

### 3. **Dashboard Frontend** (SvelteKit Admin)

#### Componentes:
- `DashboardStats.svelte`: Cards con métricas principales
- `SalesChart.svelte`: Gráfica de ventas (Chart.js)
- `StockAlerts.svelte`: Tabla de alertas de stock
- `ActiveTimers.svelte`: Vista de timers activos
- `RevenueBreakdown.svelte`: Desglose por tipo/payment

#### Páginas:
- `/admin/dashboard`: Dashboard principal
- `/admin/reports/sales`: Reportes de ventas
- `/admin/reports/stock`: Reportes de inventario
- `/admin/reports/services`: Reportes de servicios

---

## 🏗️ ARQUITECTURA

### Backend
```
packages/api/
├── routers/
│   ├── reports.py          # Nuevo: Endpoints de reportes
│   ├── users.py            # Completar: CRUD completo
│   └── ...
├── services/
│   ├── report_service.py   # Nuevo: Lógica de reportes
│   └── ...
└── models/
    └── service.py          # Actualizar: Agregar capacity
```

### Frontend
```
apps/admin/
├── src/
│   ├── routes/
│   │   ├── dashboard/
│   │   │   └── +page.svelte
│   │   ├── reports/
│   │   │   ├── sales/+page.svelte
│   │   │   ├── stock/+page.svelte
│   │   │   └── services/+page.svelte
│   │   └── users/
│   │       └── +page.svelte
│   └── lib/
│       ├── components/
│       │   ├── DashboardStats.svelte
│       │   ├── SalesChart.svelte
│       │   └── ...
│       └── api/
│           └── reports.ts  # API client para reportes
```

---

## 📝 IMPLEMENTACIÓN DETALLADA

### 1. **Report Service** (`services/report_service.py`)

```python
class ReportService:
    @staticmethod
    async def get_sales_report(
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        period: str = "day"
    ) -> dict:
        """Generate sales report with aggregations."""
        # Query sales with filters
        # Aggregate by period
        # Calculate metrics
        # Return structured data
    
    @staticmethod
    async def get_stock_report(
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        alert_only: bool = False
    ) -> dict:
        """Generate stock report with alerts and turnover."""
        # Query products
        # Calculate stock turnover
        # Identify fast/slow movers
        # Return structured data
    
    @staticmethod
    async def get_services_report(
        db: AsyncSession,
        sucursal_id: Optional[str] = None
    ) -> dict:
        """Generate services utilization report."""
        # Query active timers
        # Calculate usage hours
        # Calculate utilization rate (if capacity available)
        # Return structured data
    
    @staticmethod
    async def get_dashboard_summary(
        db: AsyncSession,
        sucursal_id: Optional[str] = None
    ) -> dict:
        """Get dashboard summary with all key metrics."""
        # Aggregate all reports
        # Return summary
```

### 2. **Reports Router** (`routers/reports.py`)

```python
router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/sales")
async def get_sales_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    period: str = "day"
):
    """Get sales report."""
    # Check permissions (super_admin, admin_viewer)
    # Call ReportService
    # Return report

@router.get("/stock")
async def get_stock_report(...):
    """Get stock report."""

@router.get("/services")
async def get_services_report(...):
    """Get services report."""

@router.get("/dashboard")
async def get_dashboard_summary(...):
    """Get dashboard summary."""
```

### 3. **Frontend API Client** (`packages/utils/src/reports.ts`)

```typescript
export async function getSalesReport(params: {
  sucursal_id?: string;
  start_date?: string;
  end_date?: string;
  period?: "day" | "week" | "month";
}): Promise<SalesReport> {
  return get("/reports/sales", params);
}

export async function getStockReport(...): Promise<StockReport> {
  return get("/reports/stock", params);
}

export async function getServicesReport(...): Promise<ServicesReport> {
  return get("/reports/services", params);
}

export async function getDashboardSummary(...): Promise<DashboardSummary> {
  return get("/reports/dashboard", params);
}
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

### Backend
- [ ] Crear `services/report_service.py`
- [ ] Crear `routers/reports.py`
- [ ] Completar `routers/users.py` (CRUD)
- [ ] Actualizar `models/service.py` (agregar capacity)
- [ ] Agregar tests para reportes
- [ ] Registrar router en `main.py`

### Frontend
- [ ] Crear `apps/admin` (si no existe)
- [ ] Crear dashboard principal
- [ ] Crear componentes de reportes
- [ ] Integrar Chart.js para gráficas
- [ ] Crear API client para reportes
- [ ] Implementar role-based routing

### Testing
- [ ] Tests de report service
- [ ] Tests de report endpoints
- [ ] Tests de frontend components

---

## 🎯 RESULTADO ESPERADO

1. ✅ **Business Logic Completo**: CRUD de usuarios funcional
2. ✅ **Dashboard Operativo**: Métricas esenciales visibles
3. ✅ **Reportes Funcionales**: Ventas, stock, servicios
4. ✅ **Frontend Integrado**: Admin panel completo
5. ✅ **Arquitectura Limpia**: Sin complejidad adicional

---

**Estado:** 🟢 **LISTO PARA IMPLEMENTACIÓN**
































