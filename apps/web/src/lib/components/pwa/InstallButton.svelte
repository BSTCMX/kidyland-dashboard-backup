<script lang="ts">
  /**
   * PWA Install Button Component
   * 
   * Displays install prompt for Progressive Web App with brutalist styling.
   * Supports both beforeinstallprompt API and iOS Safari manual install instructions.
   */
  import { onMount } from "svelte";
  import { browser } from "$app/environment";

  export let fixed = false; // Fixed positioning (bottom right)
  export let inline = false; // Inline positioning
  export let showOnlyIf = true; // Conditional visibility flag

  let deferredPrompt: any = null;
  let isInstalled = false;
  let hasInstallPrompt = false;
  
  // Browser and device detection
  let browserInfo: {
    isIOS: boolean;
    isAndroid: boolean;
    isMobile: boolean;
    isDesktop: boolean;
    isChrome: boolean;
    isFirefox: boolean;
    isSafari: boolean;
    isEdge: boolean;
    isOpera: boolean;
    isSamsungInternet: boolean;
    browserName: string;
    osName: string;
  } | null = null;

  onMount(() => {
    if (!browser) return;

    // Check if already installed (standalone mode)
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
      (window.navigator as any).standalone === true;
    isInstalled = isStandalone;

    // Detect browser and device
    const ua = window.navigator.userAgent.toLowerCase();
    const platform = (window.navigator as any).userAgentData?.platform?.toLowerCase() || 
                     window.navigator.platform.toLowerCase();
    
    browserInfo = {
      isIOS: /iphone|ipad|ipod/.test(ua) && !(window as any).MSStream,
      isAndroid: /android/.test(ua),
      isMobile: /mobile|android|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(ua),
      isDesktop: !/mobile|android|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(ua),
      isChrome: /chrome/.test(ua) && !/edg|opr|samsung/.test(ua),
      isFirefox: /firefox/.test(ua),
      isSafari: /safari/.test(ua) && !/chrome|edg|opr|samsung/.test(ua),
      isEdge: /edg/.test(ua),
      isOpera: /opr/.test(ua),
      isSamsungInternet: /samsung/.test(ua),
      browserName: (() => {
        if (/chrome/.test(ua) && !/edg|opr|samsung/.test(ua)) return 'Chrome';
        if (/firefox/.test(ua)) return 'Firefox';
        if (/safari/.test(ua) && !/chrome|edg|opr|samsung/.test(ua)) return 'Safari';
        if (/edg/.test(ua)) return 'Edge';
        if (/opr/.test(ua)) return 'Opera';
        if (/samsung/.test(ua)) return 'Samsung Internet';
        return 'Unknown';
      })(),
      osName: (() => {
        if (/iphone|ipad|ipod/.test(ua)) return 'iOS';
        if (/android/.test(ua)) return 'Android';
        if (/mac/.test(platform)) return 'macOS';
        if (/win/.test(platform)) return 'Windows';
        if (/linux/.test(platform)) return 'Linux';
        return 'Unknown';
      })(),
    };

    // Listen for beforeinstallprompt event (Chrome, Edge, Opera, Samsung Internet)
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      deferredPrompt = e;
      hasInstallPrompt = true;
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    // Check if app is already installed
    window.addEventListener('appinstalled', () => {
      isInstalled = true;
      hasInstallPrompt = false;
      deferredPrompt = null;
    });

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    };
  });

  function getInstallInstructions(): string {
    if (!browserInfo) return '';
    
    const { isIOS, isAndroid, isSafari, isFirefox, isChrome, isEdge, isOpera, isSamsungInternet, browserName, osName } = browserInfo;
    
    // iOS Safari
    if (isIOS && isSafari) {
      return 'Para instalar esta app en iOS:\n\n' +
             '1. Toca el botón de compartir (□↑) en la parte inferior\n' +
             '2. Desplázate y toca "Añadir a pantalla de inicio"\n' +
             '3. Toca "Añadir" para confirmar';
    }
    
    // Android Chrome/Edge/Opera/Samsung Internet
    if (isAndroid && (isChrome || isEdge || isOpera || isSamsungInternet)) {
      return 'Para instalar esta app en Android:\n\n' +
             '1. Toca el menú (⋮) en la esquina superior derecha\n' +
             '2. Selecciona "Instalar app" o "Añadir a pantalla de inicio"\n' +
             '3. Confirma la instalación';
    }
    
    // Android Firefox
    if (isAndroid && isFirefox) {
      return 'Para instalar esta app en Android con Firefox:\n\n' +
             '1. Toca el menú (⋮) en la esquina superior derecha\n' +
             '2. Selecciona "Instalar" o "Añadir a pantalla de inicio"\n' +
             '3. Confirma la instalación';
    }
    
    // Desktop Safari (macOS)
    if (isSafari && !isIOS) {
      return 'Para instalar esta app en macOS Safari:\n\n' +
             '1. Haz clic en "Compartir" en la barra de herramientas\n' +
             '2. Selecciona "Añadir a pantalla de inicio"\n' +
             '3. Confirma el nombre y haz clic en "Añadir"';
    }
    
    // Desktop Firefox
    if (isFirefox && !isMobile) {
      return 'Para instalar esta app en Firefox:\n\n' +
             '1. Haz clic en el icono de instalación en la barra de direcciones\n' +
             '2. O ve a Menú > Instalar esta aplicación\n' +
             '3. Confirma la instalación';
    }
    
    // Desktop Chrome/Edge/Opera
    if ((isChrome || isEdge || isOpera) && !isMobile) {
      return 'Para instalar esta app:\n\n' +
             '1. Haz clic en el icono de instalación (⊕) en la barra de direcciones\n' +
             '2. O ve a Menú > Instalar aplicación\n' +
             '3. Confirma la instalación';
    }
    
    // Generic fallback
    return `Para instalar esta app en ${browserName} (${osName}):\n\n` +
           '1. Busca el icono de instalación en la barra de direcciones\n' +
           '2. O ve al menú del navegador y busca "Instalar" o "Añadir a pantalla de inicio"\n' +
           '3. Sigue las instrucciones en pantalla';
  }

  async function installPWA() {
    if (!deferredPrompt) {
      // Show platform-specific instructions
      const instructions = getInstallInstructions();
      if (instructions) {
        alert(instructions);
      } else {
        alert('Tu navegador puede no soportar la instalación de aplicaciones web. ' +
              'Intenta usar Chrome, Edge, Firefox o Safari.');
      }
      return;
    }

    // Show install prompt (Chrome, Edge, Opera, Samsung Internet)
    try {
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;

      if (outcome === 'accepted') {
        console.log('[PWA] Usuario aceptó instalar la app');
        isInstalled = true;
      } else {
        console.log('[PWA] Usuario rechazó instalar la app');
      }
    } catch (error) {
      console.error('[PWA] Error al mostrar el prompt de instalación:', error);
      // Fallback to instructions
      const instructions = getInstallInstructions();
      if (instructions) {
        alert(instructions);
      }
    }

    deferredPrompt = null;
    hasInstallPrompt = false;
  }

  // Determine visibility
  // Show button if:
  // 1. Not already installed
  // 2. showOnlyIf is true
  // 3. Has install prompt OR is iOS Safari OR is Android (for manual instructions)
  $: shouldShow = !isInstalled && showOnlyIf && (
    hasInstallPrompt || 
    (browserInfo?.isIOS && browserInfo?.isSafari) ||
    (browserInfo?.isAndroid) ||
    (browserInfo?.isSafari && !browserInfo?.isIOS) ||
    (browserInfo?.isFirefox)
  );
</script>

{#if shouldShow}
  <button
    class="btn-install brutalist-install"
    class:fixed={fixed}
    class:inline={inline}
    on:click={installPWA}
    aria-label="Instala kidyboard"
    title="Instala kidyboard"
  >
    <span class="btn-text">Descarga</span>
    <svg class="download-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M12 5v14M5 12l7 7 7-7"/>
    </svg>
  </button>
{/if}

<style>
  /* Brutalist button base - uses global .btn-brutalist style */
  .btn-install.brutalist-install {
    /* Inherit brutalist styles from app.css */
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    min-height: var(--touch-target-min, 48px);
    min-width: 140px;
    padding: 0.75rem 1rem;
    font-family: var(--font-secondary, var(--font-primary, system-ui, sans-serif));
    font-size: var(--text-base, 16px);
    font-weight: 600;
    cursor: pointer;
    user-select: none;
    touch-action: manipulation;
    
    /* Brutalist specific styles */
    border: 2px solid var(--accent-primary);
    box-shadow: 3px 3px 0px 0px var(--accent-primary);
    background-color: var(--theme-bg-elevated);
    color: var(--accent-primary);
    border-radius: var(--radius-md);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .btn-install.brutalist-install:hover {
    box-shadow: none;
    border-width: 3px;
    transform: translate(3px, 3px);
    background-color: var(--accent-primary);
    color: var(--text-inverse);
  }

  .btn-install.brutalist-install:active {
    transform: translate(2px, 2px);
    transition-duration: 0.1s;
  }

  /* Fixed positioning */
  .btn-install.fixed {
    position: fixed;
    bottom: 1.5rem;
    right: 1.5rem;
    z-index: 1000;
  }

  @media (max-width: 768px) {
    .btn-install.fixed {
      bottom: 1rem;
      right: 1rem;
      left: auto;
    }
  }

  /* Inline positioning */
  .btn-install.inline {
    position: relative;
    display: inline-flex;
  }

  /* Button text */
  .btn-text {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100%;
  }

  /* Download icon */
  .download-icon {
    width: 18px;
    height: 18px;
    flex-shrink: 0;
    transition: transform 0.2s ease;
  }

  .btn-install.brutalist-install:hover .download-icon {
    transform: translateY(2px);
  }

  /* Mobile adjustments */
  @media (max-width: 768px) {
    .btn-install.brutalist-install {
      min-width: 120px;
      padding: 0.625rem 0.875rem;
      font-size: var(--text-sm, 14px);
    }

    .download-icon {
      width: 16px;
      height: 16px;
    }
  }

  /* Prevent hover effects on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .btn-install.brutalist-install:hover {
      transform: none;
      box-shadow: 3px 3px 0px 0px var(--accent-primary);
      border-width: 2px;
      background-color: var(--theme-bg-elevated);
      color: var(--accent-primary);
    }
  }
</style>

