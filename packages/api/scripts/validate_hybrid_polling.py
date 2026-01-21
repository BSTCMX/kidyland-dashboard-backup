#!/usr/bin/env python3
"""
Script de validación para Hybrid Intelligent Polling System.

Verifica que todos los componentes estén correctamente implementados:
- Migración de base de datos
- Modelos SQLAlchemy
- Servicios refactorizados
- Endpoints REST
- Eliminación de WebSocket
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_file_exists(filepath: str, description: str) -> bool:
    """Verificar que un archivo existe."""
    path = Path(filepath)
    exists = path.exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists

def check_file_not_exists(filepath: str, description: str) -> bool:
    """Verificar que un archivo NO existe (fue eliminado)."""
    path = Path(filepath)
    exists = path.exists()
    status = "✅" if not exists else "❌"
    print(f"{status} {description}: {filepath}")
    return not exists

def check_import(module_path: str, class_name: str) -> bool:
    """Verificar que un módulo/clase se puede importar."""
    try:
        parts = module_path.split('.')
        module = __import__(module_path)
        for part in parts[1:]:
            module = getattr(module, part)
        
        if class_name:
            getattr(module, class_name)
        
        print(f"✅ Import exitoso: {module_path}.{class_name if class_name else ''}")
        return True
    except Exception as e:
        print(f"❌ Error importando {module_path}.{class_name}: {e}")
        return False

def main():
    """Ejecutar validación completa."""
    print("=" * 60)
    print("VALIDACIÓN: HYBRID INTELLIGENT POLLING SYSTEM")
    print("=" * 60)
    print()
    
    all_checks_passed = True
    
    # 1. Verificar archivos nuevos/modificados
    print("📁 ARCHIVOS NUEVOS/MODIFICADOS")
    print("-" * 60)
    
    checks = [
        ("migrations/create_timer_alerts_table.sql", "Migración de timer_alerts"),
        ("models/timer_alert.py", "Modelo TimerAlert"),
        ("services/timer_alert_service.py", "TimerAlertService refactorizado"),
        ("routers/timers.py", "Router de timers con ETag"),
    ]
    
    for filepath, desc in checks:
        if not check_file_exists(filepath, desc):
            all_checks_passed = False
    
    print()
    
    # 2. Verificar archivos eliminados
    print("🗑️  ARCHIVOS ELIMINADOS (WebSocket)")
    print("-" * 60)
    
    removed_checks = [
        ("services/timer_broadcast_service.py", "timer_broadcast_service eliminado"),
        ("websocket/timers.py", "websocket/timers eliminado"),
        ("websocket/manager.py", "websocket/manager eliminado"),
        ("websocket/auth.py", "websocket/auth eliminado"),
        ("websocket/__init__.py", "websocket/__init__ eliminado"),
    ]
    
    for filepath, desc in removed_checks:
        if not check_file_not_exists(filepath, desc):
            all_checks_passed = False
    
    print()
    
    # 3. Verificar imports de modelos
    print("📦 IMPORTS DE MODELOS")
    print("-" * 60)
    
    import_checks = [
        ("models.timer_alert", "TimerAlert"),
        ("models.timer", "Timer"),
        ("services.timer_alert_service", "TimerAlertService"),
        ("services.timer_service", "TimerService"),
    ]
    
    for module, class_name in import_checks:
        if not check_import(module, class_name):
            all_checks_passed = False
    
    print()
    
    # 4. Verificar que main.py no tiene referencias a WebSocket
    print("🔍 VERIFICAR main.py (sin WebSocket)")
    print("-" * 60)
    
    main_py_path = Path("main.py")
    if main_py_path.exists():
        content = main_py_path.read_text()
        
        websocket_refs = [
            "from websocket",
            "import ws_timers",
            "timer_broadcast_task",
            "periodic_timer_broadcast_task",
        ]
        
        has_websocket_refs = False
        for ref in websocket_refs:
            if ref in content:
                print(f"❌ main.py contiene referencia a WebSocket: '{ref}'")
                has_websocket_refs = True
                all_checks_passed = False
        
        if not has_websocket_refs:
            print("✅ main.py no contiene referencias a WebSocket")
    else:
        print("❌ main.py no encontrado")
        all_checks_passed = False
    
    print()
    
    # 5. Verificar estructura de TimerAlertService
    print("🔧 VERIFICAR TimerAlertService")
    print("-" * 60)
    
    try:
        from services.timer_alert_service import TimerAlertService
        
        required_methods = [
            "get_pending_alerts",
            "acknowledge_alert",
            "detect_timer_alerts",
            "clear_obsolete_alerts_for_timer",
        ]
        
        for method in required_methods:
            if hasattr(TimerAlertService, method):
                print(f"✅ Método existe: TimerAlertService.{method}")
            else:
                print(f"❌ Método faltante: TimerAlertService.{method}")
                all_checks_passed = False
    except Exception as e:
        print(f"❌ Error verificando TimerAlertService: {e}")
        all_checks_passed = False
    
    print()
    
    # 6. Resumen final
    print("=" * 60)
    if all_checks_passed:
        print("✅ TODAS LAS VALIDACIONES PASARON")
        print()
        print("Sistema Hybrid Polling implementado correctamente.")
        print()
        print("Próximos pasos:")
        print("1. Ejecutar migración: psql $DATABASE_URL -f migrations/create_timer_alerts_table.sql")
        print("2. Iniciar backend: uvicorn main:app --reload")
        print("3. Iniciar frontend: cd ../../apps/web && pnpm dev")
        print("4. Verificar funcionamiento en /monitor/timers o /recepcion/timers")
        return 0
    else:
        print("❌ ALGUNAS VALIDACIONES FALLARON")
        print()
        print("Revisar los errores arriba y corregir antes de continuar.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
