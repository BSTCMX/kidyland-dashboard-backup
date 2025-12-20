# Versiones Recomendadas 2025 - Lista de Actualización

## 📦 Frontend (package.json)

```json
{
  "engines": {
    "node": ">=20.0.0",
    "pnpm": ">=9.0.0"
  },
  "packageManager": "pnpm@9.0.0",
  "devDependencies": {
    "@commitlint/cli": "^19.0.0",
    "@commitlint/config-conventional": "^19.0.0",
    "@typescript-eslint/eslint-plugin": "^8.0.0",
    "@typescript-eslint/parser": "^8.0.0",
    "concurrently": "^8.2.2",
    "eslint": "^9.0.0",
    "eslint-config-prettier": "^9.1.0",
    "eslint-plugin-import": "^2.31.0",
    "eslint-plugin-svelte": "^2.40.0",
    "husky": "^9.0.0",
    "lint-staged": "^15.2.0",
    "prettier": "^3.3.0",
    "prettier-plugin-svelte": "^3.2.0",
    "svelte-check": "^4.0.0",
    "typescript": "^5.6.0"
  }
}
```

## 🐍 Backend (requirements.txt)

```txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
sqlalchemy==2.0.36
alembic==1.13.2
pydantic==2.10.0
pydantic-settings==2.6.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
psycopg2-binary==2.9.10
```

## 🛠️ Backend Dev (requirements-dev.txt)

```txt
ruff==0.6.0
black==24.10.0
mypy==1.11.0
mypy-plugin-pydantic==0.1.0
types-psycopg2==2.9.21.14
```

## 📋 Resumen de Cambios

### 🔴 Crítico
- ruff: `0.1.6` → `0.6.0`
- Node.js: `>=18.0.0` → `>=20.0.0`
- pnpm: `8.15.0` → `9.0.0`

### 🟡 Importante
- TypeScript: `5.3.2` → `5.6.0`
- @typescript-eslint: `6.13.1` → `8.0.0`
- FastAPI: `0.104.1` → `0.115.0`
- Pydantic: `2.5.0` → `2.10.0`
- black: `23.12.1` → `24.10.0`
- mypy: `1.7.1` → `1.11.0`

### 🟢 Opcional
- ESLint: `8.54.0` → `9.0.0`
- Prettier: `3.1.0` → `3.3.0`
- commitlint: `18.4.4` → `19.0.0`
































