#!/bin/bash

# Script para verificar el estado del frontend

echo "🔍 Verificando estado del Frontend..."
echo ""

# Verificar puerto
if lsof -ti:5173 > /dev/null 2>&1; then
    echo "✅ Puerto 5173 está en uso (servidor corriendo)"
    PID=$(lsof -ti:5173 | head -1)
    echo "   PID: $PID"
else
    echo "❌ Puerto 5173 NO está en uso (servidor no corriendo)"
fi

echo ""

# Verificar procesos vite
VITE_PROCS=$(ps aux | grep -E "[v]ite|[s]velte" | wc -l | tr -d ' ')
if [ "$VITE_PROCS" -gt 0 ]; then
    echo "✅ Procesos Vite/Svelte encontrados: $VITE_PROCS"
else
    echo "❌ No se encontraron procesos Vite/Svelte"
fi

echo ""

# Verificar respuesta HTTP
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 | grep -q "200"; then
    echo "✅ Servidor responde correctamente en http://localhost:5173"
else
    echo "⏳ Servidor aún no responde o hay errores"
fi

echo ""
echo "📋 Para ver logs en tiempo real:"
echo "   tail -f /tmp/kidyland-frontend.log"
echo ""
echo "🌐 Abre en navegador:"
echo "   http://localhost:5173"

