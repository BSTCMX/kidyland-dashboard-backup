<script lang="ts">
  /**
   * Badge component - Reusable outline-style badge
   * 
   * Features:
   * - Outline style (1px border, transparent background)
   * - Consistent with 2025 design trends
   * - Supports different variants
   */
  export let variant: 'success' | 'warning' | 'danger' | 'info' | 'primary' | 'secondary' = 'secondary';
  export let size: 'sm' | 'md' | 'lg' = 'md';
</script>

<span class="badge badge-{variant} badge-{size}">
  <slot />
</span>

<style>
  .badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 500;
    border-radius: 6px;
    border: 1px solid;
    background: transparent;
    transition: all 0.2s ease;
    white-space: nowrap;
  }
  
  /* Sizes */
  .badge-sm {
    padding: 2px 6px; /* Más compacto */
    font-size: 0.6875rem; /* 11px */
    line-height: 1.2;
  }

  /* Desktop: Even more compact for table use */
  @media (min-width: 769px) {
    .badge-sm {
      padding: 0.125rem 0.375rem; /* 2px 6px */
      font-size: 0.625rem; /* 10px */
      line-height: 1.1;
    }
  }
  
  .badge-md {
    padding: 4px 12px;
    font-size: 0.875rem;
    line-height: 1.5;
  }
  
  .badge-lg {
    padding: 6px 16px;
    font-size: 1rem;
    line-height: 1.6;
  }
  
  /* Success - Green */
  .badge-success {
    border-color: #10b981;
    color: #10b981;
  }
  
  .badge-success:hover {
    background: rgba(16, 185, 129, 0.1);
  }
  
  /* Warning - Yellow/Orange */
  .badge-warning {
    border-color: #f59e0b;
    color: #f59e0b;
  }
  
  .badge-warning:hover {
    background: rgba(245, 158, 11, 0.1);
  }
  
  /* Danger - Red */
  .badge-danger {
    border-color: #ef4444;
    color: #ef4444;
  }
  
  .badge-danger:hover {
    background: rgba(239, 68, 68, 0.1);
  }
  
  /* Info - Cyan */
  .badge-info {
    border-color: #06b6d4;
    color: #06b6d4;
  }
  
  .badge-info:hover {
    background: rgba(6, 182, 212, 0.1);
  }
  
  /* Primary - Kidyland Blue */
  .badge-primary {
    border-color: #0093f7;
    color: #0093f7;
  }
  
  .badge-primary:hover {
    background: rgba(0, 147, 247, 0.1);
  }
  
  /* Secondary - Gray */
  .badge-secondary {
    border-color: #6b7280;
    color: #6b7280;
  }
  
  .badge-secondary:hover {
    background: rgba(107, 114, 128, 0.1);
  }
  
  /* Dark mode adjustments */
  :global([data-theme="dark"]) .badge {
    border-width: 1px;
  }
  
  :global([data-theme="dark"]) .badge-success {
    border-color: #34d399;
    color: #34d399;
  }
  
  :global([data-theme="dark"]) .badge-warning {
    border-color: #fbbf24;
    color: #fbbf24;
  }
  
  :global([data-theme="dark"]) .badge-danger {
    border-color: #f87171;
    color: #f87171;
  }
  
  :global([data-theme="dark"]) .badge-info {
    border-color: #22d3ee;
    color: #22d3ee;
  }
  
  :global([data-theme="dark"]) .badge-primary {
    border-color: #38bdf8;
    color: #38bdf8;
  }
  
  :global([data-theme="dark"]) .badge-secondary {
    border-color: #9ca3af;
    color: #9ca3af;
  }
</style>



