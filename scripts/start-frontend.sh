#!/bin/bash

# Script para iniciar el frontend con logging

cd /Users/Jorge/Documents/kidyland/apps/web

echo "🚀 Iniciando frontend SvelteKit..."
echo "📋 Logs en: /tmp/kidyland-frontend.log"
echo ""

# Iniciar vite con logging completo
pnpm dev 2>&1 | tee /tmp/kidyland-frontend.log

