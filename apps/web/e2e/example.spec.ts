import { test, expect } from '@playwright/test';

/**
 * Example E2E test.
 * 
 * This is a template for creating E2E tests.
 * Replace with actual test scenarios.
 */
test.describe('Example E2E Test', () => {
  test('should load the home page', async ({ page }) => {
    await page.goto('/');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Example assertion
    // Replace with actual test logic
    await expect(page).toHaveTitle(/Kidyland/i);
  });
});





























