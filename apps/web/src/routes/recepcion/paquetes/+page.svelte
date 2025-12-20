<script lang="ts">
  /**
   * Packages section page for reception.
   * 
   * Displays service packages available for sale.
   * Only shows packages that contain services (not products).
   */
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { user, canEditSecure } from "$lib/stores/auth";
  import { fetchAllPackages, packagesAdminStore } from "$lib/stores/packages-admin";
  import { filterActiveServicePackages } from "$lib/utils/package-filters";
  import type { Package } from "@kidyland/shared/types";
  import { Package as PackageIcon, Loader2, ShoppingCart } from "lucide-svelte";
  import PackageSaleForm from "$lib/components/forms/PackageSaleForm.svelte";
  import PackageSalesHistoryBar from "$lib/components/shared/PackageSalesHistoryBar.svelte";
  import { Button } from "@kidyland/ui";

  let loading = false;
  let error: string | null = null;
  let servicePackages: Package[] = [];
  let selectedPackage: Package | null = null;
  let showSaleModal = false;

  $: canCreate = canEditSecure("recepcion");

  // Get effective sucursal_id: prioritize query param, then user's sucursal_id
  // This allows super_admin to access packages with a specific sucursal via query params
  $: effectiveSucursalId = $page.url.searchParams.get('sucursal_id') || $user?.sucursal_id || null;
  $: isSuperAdmin = $user?.role === "super_admin";
  $: shouldShowError = !effectiveSucursalId && !isSuperAdmin;

  onMount(async () => {
    await loadPackages();
  });

  async function loadPackages() {
    // Allow super_admin to load packages without sucursal_id filter (shows all)
    // Other users need sucursal_id
    if (!effectiveSucursalId && !isSuperAdmin) {
      error = "No hay sucursal asignada";
      return;
    }

    loading = true;
    error = null;

    try {
      // Pass sucursal_id only if available, undefined allows fetching all (for super_admin)
      await fetchAllPackages(effectiveSucursalId || undefined);
      
      // Filter to show only active service packages
      servicePackages = filterActiveServicePackages($packagesAdminStore.list);
    } catch (e: any) {
      error = e.message || "Error al cargar paquetes";
      console.error("Error loading packages:", e);
    } finally {
      loading = false;
    }
  }

  function formatPrice(cents: number): string {
    return `$${(cents / 100).toFixed(2)}`;
  }

  function handleSellPackage(pkg: Package) {
    selectedPackage = pkg;
    showSaleModal = true;
  }

  function handleCloseModal() {
    showSaleModal = false;
    selectedPackage = null;
  }

  function handleSaleSuccess(saleId: string) {
    // Optionally reload packages or show success message
    handleCloseModal();
  }
</script>

<div class="packages-page">
  <PackageSalesHistoryBar />
  
  <div class="page-header">
    <div>
      <h1 class="page-title">Paquetes</h1>
      <p class="page-description">
        Paquetes de servicios disponibles para venta.
      </p>
    </div>
  </div>

  {#if shouldShowError}
    <div class="error-banner">No hay sucursal asignada. Por favor, selecciona una sucursal desde el panel de acceso.</div>
  {/if}

  {#if error && !shouldShowError}
    <div class="error-banner">{error}</div>
  {/if}

  {#if loading}
    <div class="loading-state">
      <Loader2 size={24} strokeWidth={1.5} class="spinner" />
      <p>Cargando paquetes...</p>
    </div>
  {:else if servicePackages.length === 0}
    <div class="empty-state">
      <PackageIcon size={48} strokeWidth={1.5} />
      <p>No hay paquetes de servicios disponibles.</p>
      <p class="empty-hint">Los paquetes se configuran desde el panel de administración.</p>
    </div>
  {:else}
    <div class="packages-grid">
      {#each servicePackages as pkg}
        <div class="package-card">
          <div class="package-header">
            <div class="package-icon">
              <PackageIcon size={24} strokeWidth={1.5} />
            </div>
            <h3 class="package-name">{pkg.name}</h3>
          </div>
          
          {#if pkg.description}
            <p class="package-description">{pkg.description}</p>
          {/if}
          
          <div class="package-price">
            {formatPrice(pkg.price_cents)}
          </div>
          
          {#if pkg.included_items && pkg.included_items.length > 0}
            <div class="package-items">
              <p class="items-label">Servicios incluidos:</p>
              <ul class="items-list">
                {#each pkg.included_items.filter((item) => item.service_id) as item}
                  <li class="item-entry">Servicio ID: {item.service_id?.slice(0, 8)}...</li>
                {/each}
              </ul>
            </div>
          {/if}

          {#if canCreate}
            <div class="package-actions">
              <Button
                variant="brutalist"
                on:click={() => handleSellPackage(pkg)}
                class="sell-button"
              >
                <ShoppingCart size={18} strokeWidth={1.5} />
                Vender
              </Button>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}

  <!-- Sale Modal -->
  {#if showSaleModal && selectedPackage}
    <div class="modal-overlay" on:click={handleCloseModal} role="dialog" aria-modal="true">
      <div class="modal-content" on:click|stopPropagation>
        <PackageSaleForm
          packageId={selectedPackage.id}
          onClose={handleCloseModal}
        />
      </div>
    </div>
  {/if}
</div>

<style>
  .packages-page {
    width: 100%;
  }

  .page-header {
    margin-bottom: var(--spacing-xl);
  }

  .page-title {
    font-family: var(--font-primary);
    font-size: var(--text-3xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md) 0;
  }

  .page-description {
    font-size: var(--text-lg);
    color: var(--text-secondary);
    margin: 0;
  }

  .error-banner {
    padding: var(--spacing-md);
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid var(--accent-danger);
    border-radius: var(--radius-md);
    color: var(--accent-danger);
    margin-bottom: var(--spacing-xl);
    text-align: center;
    font-weight: 500;
    box-shadow: 0 0 20px rgba(211, 5, 84, 0.2);
  }

  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-xl);
    gap: var(--spacing-md);
    color: var(--text-secondary);
  }

  .spinner {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-xl);
    text-align: center;
    color: var(--text-secondary);
    gap: var(--spacing-md);
  }

  .empty-hint {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    opacity: 0.7;
  }

  .packages-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: var(--spacing-xl);
  }

  .package-card {
    padding: var(--spacing-xl);
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .package-card:hover {
    transform: translateY(-4px);
    border-color: rgba(0, 147, 247, 0.5);
    box-shadow: 
      0 12px 32px rgba(0, 0, 0, 0.2),
      0 0 30px var(--glow-primary),
      0 0 40px var(--glow-secondary),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  .package-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-md);
  }

  .package-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    background: rgba(0, 147, 247, 0.1);
    border-radius: var(--radius-lg);
    color: var(--accent-primary);
  }

  .package-name {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    flex: 1;
  }

  .package-description {
    color: var(--text-secondary);
    margin: 0 0 var(--spacing-md) 0;
    line-height: 1.6;
  }

  .package-price {
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--accent-primary);
    margin-bottom: var(--spacing-md);
  }

  .package-items {
    margin-top: var(--spacing-md);
    padding-top: var(--spacing-md);
    border-top: 1px solid var(--border-primary);
  }

  .items-label {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-secondary);
    margin: 0 0 var(--spacing-sm) 0;
  }

  .items-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .item-entry {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    padding: var(--spacing-xs) var(--spacing-sm);
    background: var(--theme-bg-secondary);
    border-radius: var(--radius-sm);
  }

  .package-actions {
    margin-top: var(--spacing-md);
    padding-top: var(--spacing-md);
    border-top: 1px solid var(--border-primary);
    width: 100%;
  }

  .sell-button {
    width: 100%;
    min-height: 48px;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: var(--spacing-sm);
  }

  /* Force full width for Button component */
  .package-actions :global(button),
  .package-actions :global(.btn) {
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
  }

  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(8px) saturate(150%);
    -webkit-backdrop-filter: blur(8px) saturate(150%);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
    padding: var(--spacing-lg);
    overflow-y: auto;
  }

  .modal-content {
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    max-width: 700px;
    width: 100%;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 
      0 20px 60px rgba(0, 0, 0, 0.4),
      0 0 0 1px rgba(0, 147, 247, 0.2),
      0 0 40px var(--glow-primary),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
  }

  @media (max-width: 768px) {
    .packages-grid {
      grid-template-columns: 1fr;
      gap: var(--spacing-lg);
    }

    .page-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-sm);
    }

    .page-title {
      font-size: var(--text-2xl);
      text-align: center;
    }

    .package-card {
      padding: var(--spacing-lg);
    }

    .package-actions {
      width: 100%;
      padding-left: 0;
      padding-right: 0;
    }

    .sell-button {
      width: 100% !important;
      min-width: 100% !important;
      max-width: 100% !important;
      min-height: 44px !important; /* Minimum touch target size for accessibility */
      justify-content: center !important;
      font-size: var(--text-base) !important;
      padding: 12px 20px !important;
    }

    /* Force full width for Button component in mobile */
    .package-actions :global(button),
    .package-actions :global(.btn),
    .package-actions :global(.btn-brutalist) {
      width: 100% !important;
      min-width: 100% !important;
      max-width: 100% !important;
      min-height: 44px !important;
      justify-content: center !important;
    }

    .modal-overlay {
      padding: var(--spacing-md);
    }

    .modal-content {
      max-height: 95vh;
      border-radius: var(--radius-md);
    }
  }

  /* Tablet styles */
  @media (min-width: 769px) and (max-width: 1024px) {
    .sell-button {
      min-height: 44px;
      font-size: var(--text-base);
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .package-card:hover {
      transform: none;
    }

    .sell-button:hover {
      transform: none !important;
      box-shadow: 3px 3px 0px 0px var(--accent-primary) !important;
      border-width: 2px !important;
    }
  }
</style>

