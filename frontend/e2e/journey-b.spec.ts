import { test, expect } from '@playwright/test';

test.describe('Journey B: YouTube Batch Ingestion & Analysis Workflow', () => {
  const jobId = 'e2e-job-batch-7788';

  test.beforeEach(async ({ page }) => {
    let pollCount = 0;

    // Intercept POST /api/analyze to queue job
    await page.route('**/api/analyze', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 202,
          contentType: 'application/json',
          body: JSON.stringify({
            job_id: jobId,
            status: 'queued',
            message: 'Analysis job queued successfully',
            created_at: new Date().toISOString(),
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Intercept GET /api/analyze/:id for polling lifecycle
    await page.route(`**/api/analyze/${jobId}`, async (route) => {
      pollCount++;
      if (pollCount <= 1) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            job_id: jobId,
            status: 'running',
            progress: 0.5,
            total_comments: 50,
            processed_comments: 25,
            video: {
              video_id: 'L0yEMl8PXnw',
              title: 'Aavesham Official Trailer — Fahadh Faasil | Jithu Madhavan | Sushin Shyam',
              channel_title: 'Anwar Rasheed Entertainments',
              view_count: 14850000,
            },
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            job_id: jobId,
            status: 'completed',
            progress: 1.0,
            total_comments: 50,
            processed_comments: 50,
            video: {
              video_id: 'L0yEMl8PXnw',
              title: 'Aavesham Official Trailer — Fahadh Faasil | Jithu Madhavan | Sushin Shyam',
              channel_title: 'Anwar Rasheed Entertainments',
              view_count: 14850000,
            },
            summary: {
              total_analyzed: 50,
              sentiment_counts: {
                positive: 35,
                negative: 5,
                neutral: 6,
                mixed: 4,
                unsupported: 0,
              },
              sentiment_percentages: {
                positive: 70.0,
                negative: 10.0,
                neutral: 12.0,
                mixed: 8.0,
                unsupported: 0.0,
              },
            },
          }),
        });
      }
    });
  });

  test('submits YouTube URL, observes pipeline progress, and navigates to audience dashboard', async ({ page }) => {
    await page.goto('/analyze');

    // Verify analyze page title
    await expect(page.getByRole('heading', { name: /YouTube Comment Analysis/i })).toBeVisible();

    // Input YouTube URL
    const urlInput = page.getByLabel(/YouTube Video URL/i);
    await urlInput.fill('https://www.youtube.com/watch?v=L0yEMl8PXnw');

    // Submit ingestion job
    const submitBtn = page.getByRole('button', { name: /Start Ingestion & Analysis/i });
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click();

    // Verify Pipeline Execution Panel activates
    await expect(page.getByTestId('analyze-progress-panel')).toBeVisible();

    // Verify completion status and stage progress
    await expect(page.getByText('Analysis Complete')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('100%')).toBeVisible();

    // Verify "View Audience Dashboard" button appears
    const viewDashboardBtn = page.getByRole('button', { name: /View Audience Dashboard/i });
    await expect(viewDashboardBtn).toBeVisible();

    // Click to navigate to the dashboard
    await viewDashboardBtn.click();
    await expect(page).toHaveURL(new RegExp(`/dashboard\\?job_id=${jobId}`));
  });
});
