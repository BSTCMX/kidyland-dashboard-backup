# 🚀 PROMPT 8B - Plan de Implementación Híbrido

**Objetivo:** Business Logic Completo + Analytics Dashboard Sofisticado (sin over-engineering)

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

## 📊 PARTE B: Analytics & Dashboard (Enfoque Híbrido)

### **FASE 1: Fundación Sólida (Implementar ahora)**

#### 1. **Modelos Actualizados**

**Service Model:**
```python
# Agregar a models/service.py:
max_capacity = Column(Integer, nullable=True)  # Capacidad máxima simultánea
operating_hours_start = Column(Time, nullable=True)
operating_hours_end = Column(Time, nullable=True)
```

**Product Model:**
```python
# Agregar a models/product.py:
cost_cents = Column(Integer, nullable=True)  # Costo para profit margin
```

**Customer Model (Nuevo):**
```python
# Crear models/customer.py:
class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(UUID, primary_key=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relación opcional con sales (para futuro)
    # sales = relationship("Sale", back_populates="customer")
```

#### 2. **Analytics Service**

**services/report_service.py:**
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
        """
        Generate sales report with aggregations.
        
        Returns:
            {
                "total_revenue_cents": int,
                "average_transaction_value_cents": int,
                "sales_count": int,
                "revenue_by_type": dict,
                "revenue_by_sucursal": dict,
                "revenue_by_payment_method": dict
            }
        """
        # Query optimizada con agregaciones SQL
        # Sin Redis (PostgreSQL directo)
    
    @staticmethod
    async def get_stock_report(...) -> dict:
        """Stock metrics: Alerts, Turnover, Fast/Slow Movers"""
    
    @staticmethod
    async def get_services_report(...) -> dict:
        """Services metrics: Active, Usage Hours, Utilization Rate"""
    
    @staticmethod
    async def get_dashboard_summary(...) -> dict:
        """Dashboard summary: All key metrics"""
```

#### 3. **Reports Router**

**routers/reports.py:**
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
    require_role(["super_admin", "admin_viewer"])(current_user)
    return await ReportService.get_sales_report(...)

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

#### 4. **WebSocket Analytics**

**websocket/analytics.py:**
```python
@router.websocket("/ws/analytics")
async def analytics_websocket(
    websocket: WebSocket,
    token: str = Query(...),
    sucursal_id: str = Query(...)
):
    """WebSocket para métricas en tiempo real."""
    # Reutiliza ConnectionManager existente
    # Broadcast de métricas actualizadas cada 10-30s
    # Reconexión con exponential backoff
```

#### 5. **Cache Interface (Sin Redis aún)**

**services/analytics_cache.py:**
```python
class AnalyticsCache:
    """
    Cache interface for analytics metrics.
    
    Currently uses in-memory cache (dict).
    Designed to easily swap to Redis later.
    """
    
    def __init__(self):
        self._cache: dict = {}
        self._ttl: dict = {}
    
    async def get(self, key: str) -> Optional[dict]:
        """Get cached value."""
        # In-memory implementation
        # TODO: Swap to Redis when needed
    
    async def set(self, key: str, value: dict, ttl: int = 300):
        """Set cached value."""
        # In-memory implementation
        # TODO: Swap to Redis when needed
```

---

### **FASE 2: Dashboard Frontend**

#### 1. **Dashboard Principal**

**apps/admin/src/routes/dashboard/+page.svelte:**
```svelte
<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getDashboardSummary } from "@kidyland/utils/reports";
  import DashboardStats from "$lib/components/DashboardStats.svelte";
  import SalesChart from "$lib/components/SalesChart.svelte";
  import StockAlerts from "$lib/components/StockAlerts.svelte";
  import ServiceUtilization from "$lib/components/ServiceUtilization.svelte";
  
  // WebSocket para updates real-time
  // Gráficas con Chart.js
  // Filtros: fecha, sucursal, tipo
</script>
```

#### 2. **Componentes Reutilizables**

**DashboardStats.svelte:**
- Cards con métricas principales
- Total Revenue, ATV, Sales Count
- Active Timers, Low Stock Alerts

**SalesChart.svelte:**
- Gráfica de ventas (Chart.js)
- Filtros por periodo (día/semana/mes)
- Desglose por tipo

**StockAlerts.svelte:**
- Tabla de alertas de stock
- Fast/Slow movers
- Stock turnover

**ServiceUtilization.svelte:**
- Timers activos
- Utilization rate
- Peak hours

#### 3. **API Client**

**packages/utils/src/reports.ts:**
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

## 🚫 LO QUE NO IMPLEMENTAREMOS AÚN

### **Diferir hasta tener datos suficientes:**
- ❌ Anomaly Detection (requiere 3-6 meses de datos)
- ❌ Forecasting (requiere patrones históricos)
- ❌ Customer Analytics avanzado (requiere sistema completo)

### **Diferir hasta tener necesidad real:**
- ❌ Redis (agregar cuando >50 usuarios o queries >500ms)
- ❌ Background jobs pesados (agregar cuando haya necesidad)

---

## ✅ CHECKLIST COMPLETO

### **Backend**
- [ ] Actualizar `models/service.py` (max_capacity, operating_hours)
- [ ] Actualizar `models/product.py` (cost_cents)
- [ ] Crear `models/customer.py` (estructura básica)
- [ ] Crear `services/report_service.py`
- [ ] Crear `services/analytics_cache.py` (interfaz, sin Redis)
- [ ] Crear `routers/reports.py`
- [ ] Crear `websocket/analytics.py`
- [ ] Completar `routers/users.py` (CRUD)
- [ ] Agregar tests para report service
- [ ] Agregar tests para report endpoints
- [ ] Registrar router en `main.py`

### **Frontend**
- [ ] Crear/actualizar `apps/admin`
- [ ] Crear dashboard principal
- [ ] Crear componentes de reportes
- [ ] Integrar Chart.js o ApexCharts
- [ ] Integrar WebSocket analytics
- [ ] Crear stores para métricas
- [ ] Implementar filtros (fecha, sucursal, tipo)
- [ ] Completar flujos de venta (Reception, KidiBar)

### **Testing**
- [ ] Tests de report service
- [ ] Tests de report endpoints
- [ ] Tests de WebSocket analytics
- [ ] Tests de frontend components

---

## 🎯 RESULTADO ESPERADO

1. ✅ **Business Logic Completo**: CRUD de usuarios funcional
2. ✅ **Dashboard Operativo**: Métricas esenciales visibles
3. ✅ **Reportes Funcionales**: Ventas, stock, servicios
4. ✅ **Frontend Integrado**: Admin panel completo
5. ✅ **Arquitectura Limpia**: Sin complejidad adicional innecesaria
6. ✅ **Preparado para Escalar**: Fácil agregar Redis, forecasting, etc.

---

**Estado:** 🟢 **LISTO PARA IMPLEMENTACIÓN CON ENFOQUE HÍBRIDO**
































