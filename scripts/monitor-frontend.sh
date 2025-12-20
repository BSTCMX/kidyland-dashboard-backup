#!/bin/bash

# Script para monitorear el frontend y capturar errores

echo "🔍 Iniciando monitoreo del frontend..."
echo ""

# Verificar si el servidor está corriendo
if ! lsof -ti:5173 > /dev/null 2>&1; then
    echo "⚠️  Servidor no está corriendo. Iniciando..."
    cd /Users/Jorge/Documents/kidyland/apps/web
    pnpm dev > /tmp/kidyland-frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "   PID: $FRONTEND_PID"
    echo "   Esperando 5 segundos para que inicie..."
    sleep 5
else
    echo "✅ Servidor ya está corriendo en puerto 5173"
    FRONTEND_PID=$(lsof -ti:5173 | head -1)
    echo "   PID: $FRONTEND_PID"
fi

echo ""
echo "📋 Monitoreando logs en tiempo real..."
echo "   Presiona Ctrl+C para detener"
echo ""
echo "========================================="
echo ""

# Monitorear logs
tail -f /tmp/kidyland-frontend.log 2>/dev/null || echo "⚠️  Archivo de log no encontrado. Ejecutando servidor directamente..."

