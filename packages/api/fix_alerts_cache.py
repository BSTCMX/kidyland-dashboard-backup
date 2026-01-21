"""
Fix: Limpiar alertas del caché cuando timer sale del rango de threshold.

El problema es que _sent_alerts mantiene alertas indefinidamente, bloqueando reenvíos.
La solución es limpiar alertas que ya no aplican (timer fuera del rango).
"""

# Agregar lógica de limpieza en detect_timer_alerts:
# Antes de procesar alertas, limpiar las que ya no aplican

print("""
SOLUCIÓN:

En timer_alert_service.py, después de línea 182 (cleanup), agregar:

# Clear sent alerts for timers that are no longer in threshold range
for timer_data in timers_data:
    timer_id = timer_data["id"]
    time_left_minutes = timer_data.get("time_left_minutes", 0)
    
    # Clear alerts for thresholds that timer has passed
    # (timer is now below threshold - 2 minutes)
    alerts_to_clear = [
        (timer_id, alert_min)
        for (tid, alert_min) in TimerAlertService._sent_alerts
        if tid == timer_id and time_left_minutes < (alert_min - 2)
    ]
    
    for alert_key in alerts_to_clear:
        TimerAlertService._sent_alerts.discard(alert_key)
        logger.debug(f"Cleared sent alert: {alert_key}")
""")
