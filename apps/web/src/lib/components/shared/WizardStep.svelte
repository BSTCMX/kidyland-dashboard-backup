<script lang="ts">
  /**
   * WizardStep component - Reusable wrapper for wizard steps.
   * 
   * Provides consistent styling and structure for multi-step forms.
   */
  import { createEventDispatcher } from "svelte";
  import { ChevronRight, ChevronLeft } from "lucide-svelte";

  const dispatch = createEventDispatcher();

  export let stepNumber: number;
  export let totalSteps: number;
  export let title: string;
  export let description: string | undefined = undefined;
  export let canGoNext: boolean = true;
  export let canGoBack: boolean = true;
  export let showNavigation: boolean = true;

  function handleNext() {
    if (canGoNext) {
      dispatch("next");
    }
  }

  function handleBack() {
    if (canGoBack) {
      dispatch("back");
    }
  }
</script>

<div class="wizard-step">
  <div class="step-header">
    <div class="step-indicator">
      <span class="step-number">{stepNumber}</span>
      <span class="step-divider">/</span>
      <span class="total-steps">{totalSteps}</span>
    </div>
    <div class="step-info">
      <h2 class="step-title">{title}</h2>
      {#if description}
        <p class="step-description">{description}</p>
      {/if}
    </div>
  </div>

  <div class="step-content">
    <slot />
  </div>

  {#if showNavigation}
    <div class="step-navigation">
      <button
        type="button"
        class="nav-button back-button"
        on:click={handleBack}
        disabled={!canGoBack || stepNumber === 1}
      >
        <ChevronLeft size={18} strokeWidth={1.5} />
        Anterior
      </button>

      <button
        type="button"
        class="nav-button next-button"
        on:click={handleNext}
        disabled={!canGoNext}
      >
        Siguiente
        <ChevronRight size={18} strokeWidth={1.5} />
      </button>
    </div>
  {/if}
</div>

<style>
  .wizard-step {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
    padding: var(--spacing-xl);
    background: var(--theme-bg-elevated);
    border-radius: var(--radius-lg);
    border: 1px solid var(--border-primary);
    min-height: 400px;
  }

  .step-header {
    display: flex;
    align-items: flex-start;
    gap: var(--spacing-md);
    padding-bottom: var(--spacing-md);
    border-bottom: 2px solid var(--border-primary);
  }

  .step-indicator {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--accent-primary);
    padding: var(--spacing-sm) var(--spacing-md);
    background: rgba(0, 147, 247, 0.1);
    border-radius: var(--radius-md);
    min-width: 80px;
    justify-content: center;
  }

  .step-number {
    font-size: var(--text-xl);
  }

  .step-divider {
    opacity: 0.5;
  }

  .total-steps {
    font-size: var(--text-base);
    opacity: 0.7;
  }

  .step-info {
    flex: 1;
  }

  .step-title {
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-xs) 0;
    
    /* Brutalist 3D text shadow */
    text-shadow: 
      0 0.05em 0 rgba(0, 0, 0, 0.1),
      0 0.1em 0 rgba(0, 0, 0, 0.1),
      0 0.15em 0 rgba(0, 0, 0, 0.1),
      0 0.2em 0 rgba(0, 0, 0, 0.1);
  }

  .step-description {
    font-size: var(--text-base);
    color: var(--text-secondary);
    margin: 0;
  }

  .step-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    min-height: 0; /* Critical: allows scroll in flex children */
    overflow-y: auto; /* Enable scroll for content that exceeds height */
    overflow-x: hidden; /* Prevent horizontal scroll */
    /* Touch scrolling optimizations for mobile */
    touch-action: pan-y;
    -webkit-overflow-scrolling: touch;
  }

  .step-navigation {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--spacing-md);
    padding-top: var(--spacing-md);
    border-top: 1px solid var(--border-primary);
  }

  .nav-button {
    /* Use form button styles for consistency */
    background-color: var(--accent-primary, #08d);
    border-radius: 12px;
    border: 0;
    box-sizing: border-box;
    color: #eee;
    cursor: pointer;
    font-size: 18px;
    height: 50px;
    text-align: center;
    width: auto;
    min-width: 120px;
    padding: 0 24px;
    font-family: var(--font-body, sans-serif);
    font-weight: 600;
    transition: background-color 0.2s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }

  .back-button {
    /* Secondary button style */
    background: linear-gradient(to bottom, #f5f5f5, #e6e6e6);
    background-color: #e6e6e6;
    border-color: #d4d4d4;
    color: #333333;
    text-shadow: 0 1px 1px rgba(255, 255, 255, 0.75);
  }

  .back-button:hover:not(:disabled) {
    background: linear-gradient(to bottom, #ffffff, #f5f5f5);
    background-color: #f5f5f5;
    border-color: #d4d4d4;
  }

  .back-button:active:not(:disabled) {
    background: linear-gradient(to bottom, #e6e6e6, #d4d4d4);
    background-color: #d4d4d4;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .next-button {
    /* Primary button style */
    background: linear-gradient(to bottom, #6eb6de, #4a77d4);
    background-color: #4a77d4;
    border-color: #3762bc;
    color: #ffffff;
    text-shadow: 0 -1px 0 rgba(0, 0, 0, 0.25);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2), 0 1px 2px rgba(0, 0, 0, 0.2);
    margin-left: auto;
  }

  .next-button:hover:not(:disabled) {
    background: linear-gradient(to bottom, #7fc3e5, #5a87e4);
    background-color: #5a87e4;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2), 0 2px 4px rgba(0, 0, 0, 0.3);
    transform: none; /* Remove translateY for consistency */
  }

  .next-button:active:not(:disabled) {
    background: linear-gradient(to bottom, #4a77d4, #3762bc);
    background-color: #3762bc;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  .nav-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .wizard-step {
      padding: var(--spacing-md);
      min-height: auto;
    }

    .step-header {
      flex-direction: column;
      align-items: flex-start;
    }

    .step-indicator {
      align-self: flex-start;
    }

    .step-title {
      font-size: var(--text-xl);
    }

    .step-navigation {
      flex-direction: column;
      width: 100%;
    }

    .nav-button {
      width: 100%;
      justify-content: center;
    }

    .next-button {
      margin-left: 0;
    }
  }

  /* Responsive adjustments for buttons */
  @media (max-width: 768px) {
    .nav-button {
      width: 100%;
      min-width: auto;
    }

    .next-button {
      margin-left: 0;
    }
  }
</style>
