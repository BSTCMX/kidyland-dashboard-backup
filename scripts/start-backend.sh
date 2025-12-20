#!/bin/bash

# Script para iniciar el backend con logging

cd /Users/Jorge/Documents/kidyland/packages/api

# Activar venv si existe
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

echo "🚀 Iniciando backend FastAPI..."
echo "📋 Logs en: /tmp/kidyland-backend.log"
echo ""

# Iniciar uvicorn con logging completo
uvicorn main:app --reload --host 0.0.0.0 --port 8000 2>&1 | tee /tmp/kidyland-backend.log

