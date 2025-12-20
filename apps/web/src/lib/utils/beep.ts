/**
 * Beep utility functions for audio notifications.
 * 
 * Provides simple beep/alert sound functionality.
 * Currently not actively used - sound alerts are handled in timers store.
 */

/**
 * Play a beep sound using the alert audio file.
 * 
 * @param loop - Whether to loop the sound (default: false)
 */
export function beep(loop: boolean = false): void {
  if (typeof window === "undefined") {
    return; // SSR safety
  }

  const audio = new Audio("/sounds/alert.mp3");
  audio.loop = loop;
  audio.play().catch((err) => {
    console.error("Error playing beep:", err);
  });
}

/**
 * Stop a beep sound (if looping).
 * Note: This is a simple implementation. For better control,
 * use the timer alert sound functions in timers store.
 */
export function stopBeep(): void {
  // This is a placeholder - in practice, sound control
  // is handled by the timers store which manages Audio elements
  console.warn("stopBeep() called - use timers store for sound control");
}
