<script lang="ts">
  /**
   * Video Export page - Generate animated menu videos.
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { user, hasAccessSecure, canEditSecure } from "$lib/stores/auth";
  import MenuWizard from "$lib/components/shared/MenuWizard.svelte";
  import { Video } from "lucide-svelte";

  onMount(() => {
    // Verify user has access to admin - uses secure checks that verify token-store consistency
    if (!$user || !hasAccessSecure("/admin") || !canEditSecure("admin")) {
      goto("/");
      return;
    }
  });

  function handleExported(event: CustomEvent) {
    console.log("Export completed:", event.detail);
    // Could show a success notification here
  }

  function handleError(event: CustomEvent<{ error: string }>) {
    // Extract error message from event detail
    const errorMessage = event.detail?.error || "Error desconocido al exportar";
    console.error("Export error:", errorMessage);
    // Could show an error notification here
  }
</script>

<div class="video-export-page">
  <div class="page-header">
    <h1 class="page-title">
      <Video size={32} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 12px;" />
      Exportar Video de Menú
    </h1>
    <p class="page-description">
      Genera un video animado o PDF con branding Kidyland mostrando servicios y productos.
      Perfecto para pantallas digitales en centros comerciales.
    </p>
  </div>

  <MenuWizard
    width={1920}
    height={1080}
    fps={25}
    on:exported={handleExported}
    on:error={handleError}
  />
</div>

<style>
  .video-export-page {
    min-height: 100vh;
    background: var(--theme-bg-primary);
    padding: var(--spacing-xl);
  }

  .page-header {
    margin-bottom: var(--spacing-xl);
  }

  .page-title {
    font-family: var(--font-primary);
    font-size: var(--text-3xl);
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: var(--spacing-md);
    display: flex;
    align-items: center;
    
    /* Brutalist 3D text shadow effect */
    text-shadow: 
      0 0.05em 0 rgba(0, 0, 0, 0.1),
      0 0.1em 0 rgba(0, 0, 0, 0.1),
      0 0.15em 0 rgba(0, 0, 0, 0.1),
      0 0.2em 0 rgba(0, 0, 0, 0.1),
      0 0.25em 0 rgba(0, 0, 0, 0.1),
      0 0.25em 0.02em rgba(0, 0, 0, 0.15),
      0 0.28em 0.2em rgba(0, 0, 0, 0.25);
  }

  .page-description {
    font-size: var(--text-base);
    color: var(--text-secondary);
    max-width: 800px;
  }

  @media (max-width: 768px) {
    .video-export-page {
      padding: var(--spacing-md);
    }

    .page-title {
      font-size: var(--text-2xl);
      text-align: center;
      justify-content: center;
      flex-wrap: wrap;
    }

    .page-title :global(svg) {
      margin-right: 8px;
      margin-bottom: 4px;
    }
  }
</style>
