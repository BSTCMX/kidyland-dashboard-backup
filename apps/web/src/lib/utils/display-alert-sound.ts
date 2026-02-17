/**
 * Vista Display: play alert sound when timer reaches 0.
 * Reuses shared alert asset (same as timers, beep, ServiceForm).
 */
import type { ZeroAlertConfig } from "@kidyland/shared/types";
import { ALERT_SOUND_SRC } from "$lib/constants/assets";
let zeroAlertAudio: HTMLAudioElement | null = null;
let zeroAlertLoopTimeoutId: number | null = null;

function getAudio(): HTMLAudioElement {
  if (!zeroAlertAudio) {
    zeroAlertAudio = new Audio(ALERT_SOUND_SRC);
  }
  return zeroAlertAudio;
}

/**
 * Play zero-alert sound (timer reached 0) in Vista Display.
 * If config.sound_loop, loops until stopZeroAlertSound() is called.
 */
export function playZeroAlertSound(config: ZeroAlertConfig): void {
  if (!config.sound_enabled) return;

  console.log("[Display] playZeroAlertSound called", { sound_loop: config.sound_loop });
  const audio = getAudio();
  if (zeroAlertLoopTimeoutId != null) {
    clearTimeout(zeroAlertLoopTimeoutId);
    zeroAlertLoopTimeoutId = null;
  }

  audio.loop = config.sound_loop || false;
  audio.currentTime = 0;
  audio.play().catch((err) => {
    console.error("[Display] Error playing zero alert sound:", err);
    if (err?.name === "NotAllowedError") {
      console.warn("[Display] Audio blocked by browser (user gesture required). Interact with the page first.");
    }
  });
}

/**
 * Stop the zero-alert sound (e.g. when finished message is dismissed or after duration).
 */
export function stopZeroAlertSound(): void {
  if (zeroAlertLoopTimeoutId != null) {
    clearTimeout(zeroAlertLoopTimeoutId);
    zeroAlertLoopTimeoutId = null;
  }
  if (zeroAlertAudio) {
    zeroAlertAudio.pause();
    zeroAlertAudio.currentTime = 0;
  }
}

/**
 * Schedule stopping the zero-alert sound after a delay (e.g. FINISHED_MESSAGE_DURATION).
 */
export function scheduleStopZeroAlertSoundAfter(ms: number): void {
  if (zeroAlertLoopTimeoutId != null) clearTimeout(zeroAlertLoopTimeoutId);
  zeroAlertLoopTimeoutId = window.setTimeout(() => {
    stopZeroAlertSound();
    zeroAlertLoopTimeoutId = null;
  }, ms);
}
