#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from database import engine
from models.day_start import DayStart
from uuid import UUID

async def check():
    async with engine.connect() as conn:
        sucursal_id = UUID('f65f4767-e355-4229-8297-a8d476adc69f')
        result = await conn.execute(
            select(DayStart).where(
                DayStart.sucursal_id == sucursal_id,
                DayStart.is_active == True
            )
        )
        day = result.scalar_one_or_none()
        if day:
            print(f'✅ HAY DÍA ACTIVO: ID={day.id}, Started={day.started_at}')
        else:
            print('❌ NO HAY DÍA ACTIVO')

asyncio.run(check())






