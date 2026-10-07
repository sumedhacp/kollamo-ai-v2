import { test, expect } from '@playwright/test';

test.describe('Journey A: Live Sentiment Sandbox Inference', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept /api/sentiment for predictable, ultra-fast E2E verification
    await page.route('**/api/sentiment', async (route) => {
      const request = route.request();
      const postData = JSON.parse(request.postData() || '{}');

      if (!postData.text) {
        await route.fulfill({
          status: 422,
          contentType: 'application/json',
          body: JSON.stringify({
            error: {
              code: 'VALIDATION_ERROR',
              message: 'Request validation failed',
              details: [{ loc: ['body', 'text'], msg: 'Field required' }],
            },
          }),
        });
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          original_text: postData.text,
          detected_language: 'ml-en',
          detected_script: 'Latin',
          sentiment: 'positive',
          confidence: 0.965,
          class_probabilities: {
            positive: 0.965,
            negative: 0.012,
            neutral: 0.011,
            mixed: 0.008,
            unsupported: 0.004,
          },
          translation_status: postData.translate ? 'translated' : 'skipped',
          translated_text: postData.translate
            ? 'The movie was amazing, Fahadh Faasil gave a next-level performance!'
            : null,
        }),
      });
    });
  });

  test('completes end-to-end comment evaluation, script detection, and translation', async ({ page }) => {
    await page.goto('/sandbox');

    // Verify Sandbox page elements
    await expect(page.getByRole('heading', { name: /Comment Sentiment Sandbox/i })).toBeVisible();
    await expect(page.getByLabel(/Comment text for sentiment analysis/i)).toBeVisible();

    // Verify button is initially disabled
    const analyzeBtn = page.getByRole('button', { name: /Analyze Sentiment/i });
    await expect(analyzeBtn).toBeDisabled();

    // Enter Manglish review text
    const commentInput = page.getByLabel(/Comment text for sentiment analysis/i);
    await commentInput.fill('Padam kidilan aayirunnu, Fahadh Faasil vere level performance!');

    // Enable English translation
    const translateToggle = page.locator('#translate-toggle');
    if (!(await translateToggle.isChecked())) {
      await translateToggle.check();
    }
    await expect(translateToggle).toBeChecked();

    // Click Analyze Sentiment
    await expect(analyzeBtn).toBeEnabled();
    await analyzeBtn.click();

    // Verify Results Card is rendered
    await expect(page.getByTestId('sandbox-result-state')).toBeVisible();
    await expect(page.getByText('positive')).toBeVisible();
    await expect(page.getByText('96.5%')).toBeVisible();

    // Verify Detected Script & Language Badges
    await expect(page.getByText('Latin')).toBeVisible();
    await expect(page.getByText('ml-en')).toBeVisible();

    // Verify English translation card rendered
    await expect(
      page.getByText(/The movie was amazing, Fahadh Faasil gave a next-level performance!/i)
    ).toBeVisible();
  });
});
