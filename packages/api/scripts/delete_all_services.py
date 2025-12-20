#!/usr/bin/env python3
"""
Script para eliminar todos los servicios existentes (hard delete).

⚠️ ADVERTENCIA: Esta acción es IRREVERSIBLE.
Elimina permanentemente todos los servicios de la base de datos.

Uso:
    python3 scripts/delete_all_services.py

Requisitos:
    - Archivo .env con DATABASE_URL configurado
    - SQLAlchemy ya está instalado (parte de requirements.txt)
"""
import asyncio
import sys
from pathlib import Path

# Agregar el directorio actual al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, delete
from database import engine
from models.service import Service


async def delete_all_services():
    """
    Elimina permanentemente todos los servicios de la base de datos.
    """
    print("=" * 70)
    print("⚠️  ELIMINACIÓN PERMANENTE DE TODOS LOS SERVICIOS")
    print("=" * 70)
    print()
    print("ADVERTENCIA: Esta acción es IRREVERSIBLE.")
    print("Todos los servicios serán eliminados permanentemente.")
    print()
    
    # Confirmar antes de proceder
    response = input("¿Estás seguro de que deseas continuar? (escribe 'SI' para confirmar): ")
    if response != "SI":
        print("Operación cancelada.")
        sys.exit(0)
    
    print()
    print("🔌 Conectando a base de datos...")
    
    try:
        # Contar servicios antes de eliminar
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM services"))
            count_before = result.scalar_one()
            print(f"📊 Servicios encontrados: {count_before}")
        
        if count_before == 0:
            print("✅ No hay servicios para eliminar.")
            return
        
        # Eliminar todos los servicios
        async with engine.begin() as conn:
            print("🗑️  Eliminando todos los servicios...")
            await conn.execute(delete(Service))
            print("   ✅ Servicios eliminados")
        
        # Verificar eliminación
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM services"))
            count_after = result.scalar_one()
            print(f"📊 Servicios restantes: {count_after}")
        
        if count_after == 0:
            print()
            print("=" * 70)
            print("🎉 ELIMINACIÓN COMPLETADA EXITOSAMENTE")
            print("=" * 70)
            print(f"✅ Se eliminaron {count_before} servicios permanentemente.")
        else:
            print()
            print("⚠️  ADVERTENCIA: Quedan servicios en la base de datos.")
            print(f"   Esperado: 0, Encontrado: {count_after}")
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERROR AL ELIMINAR SERVICIOS")
        print("=" * 70)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(delete_all_services())


















