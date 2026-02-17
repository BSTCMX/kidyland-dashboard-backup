# Sonidos compartidos

Esta carpeta contiene el asset de alerta usado en toda la app.

- **`alert.mp3`** – Ruta pública: `/sounds/alert.mp3`  
  Consumido por: Vista Display (alerta al llegar a 0), store de timers (alertas por minuto), utilidad beep y preview en formulario de servicios (admin).  
  La ruta está centralizada en `$lib/constants/assets.ts` (`ALERT_SOUND_SRC`).
