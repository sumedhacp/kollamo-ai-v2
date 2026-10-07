import { test, expect } from '@playwright/test';

test.describe('Journey C: Audience Intelligence Dashboard & Reporting', () => {
  test('explores Net Approval, filters sentiments, switches chart views, and downloads PDF report', async ({ page }) => {
    // Navigate to dashboard using the built-in demo dataset
    await page.goto('/dashboard?job_id=demo-aavesham-2026-sample');

    // 1. Verify Video Header & Meta Intelligence
    await expect(page.getByText('Aavesham Official Trailer')).toBeVisible();
    await expect(page.getByText('Anwar Rasheed Entertainments')).toBeVisible();

    // 2. Verify Net Approval Index
    await expect(page.getByText('Audience Net Approval Index:')).toBeVisible();
    await expect(page.getByText('+60%')).toBeVisible();
    await expect(page.getByText('Overwhelmingly Positive')).toBeVisible();

    // 3. Switch between 5-Class Share and Scripts chart views
    await expect(page.getByText('5-Class Share')).toBeVisible();
    const scriptsTab = page.getByRole('button', { name: 'Scripts' });
    await scriptsTab.click();
    await expect(page.getByText('Malayalam Script')).toBeVisible();
    await expect(page.getByText(/Latin Script \(Manglish \/ English\)/i)).toBeVisible();

    // Switch back to distribution
    const distTab = page.getByRole('button', { name: '5-Class Share' });
    await distTab.click();

    // 4. Test Sentiment Filtering in Comment Explorer
    const negativeFilter = page.getByRole('button', { name: /negative/i });
    await negativeFilter.click();
    await expect(page.getByText(/Valare mosham direction/i)).toBeVisible();
    await expect(page.getByText(/Sreejith Menon/i)).toBeVisible();

    // 5. Test Search Filtering
    const searchInput = page.getByPlaceholderText(/Search comments or author\.\.\./i);
    await searchInput.fill('Fahadh');
    await expect(page.getByText(/Fahadh/i)).toBeVisible();

    // 6. Test Academic PDF Export
    const exportPdfBtn = page.getByRole('button', { name: /Export PDF Report/i });
    await expect(exportPdfBtn).toBeVisible();
    await exportPdfBtn.click();

    // Verify feedback notification
    await expect(
      page.getByText(/Academic PDF report compiled and downloaded successfully!/i)
    ).toBeVisible({ timeout: 5000 });
  });
});
