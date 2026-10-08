/**
 * Client-Side PDF Report Generator for Kollamo.ai (Phase 8).
 *
 * Compiles a comprehensive, publication-quality academic
 * Audience Intelligence Report using jsPDF.
 */

import { jsPDF } from 'jspdf';
import { AnalysisJob, CommentItem } from '@/types';

export interface PdfReportOptions {
  includeMethodology?: boolean;
  includeComments?: boolean;
  maxComments?: number;
  reportTitle?: string;
  sampleSize?: number | string;
  sortMode?: string;
  modelName?: string;
  modelVersion?: string;
  processingTime?: string;
}

/**
 * Sanitizes YouTube video identifier for safe file system naming.
 */
export function sanitizeVideoId(videoId?: string): string {
  if (!videoId) return 'video';
  return videoId.replace(/[^a-zA-Z0-9_-]/g, '').slice(0, 40) || 'video';
}

/**
 * Generates the standardized filename according to Phase 8 Section 31:
 * kollamo-ai-analysis-<video-id>.pdf
 */
export function getAnalysisReportFilename(videoId?: string): string {
  const cleanId = sanitizeVideoId(videoId);
  return `kollamo-ai-analysis-${cleanId}.pdf`;
}

/**
 * Renders Malayalam Unicode text into the PDF cleanly.
 * In a browser environment, uses high-DPI HTML5 canvas font rendering to preserve ligatures and glyph shaping.
 * In headless/Node test environments, safely falls back to standard text rendering.
 */
function renderMalayalamTextToPdf(
  doc: jsPDF,
  text: string,
  x: number,
  y: number,
  maxWidthMm: number,
  fontSizePt: number = 8,
  textColor: [number, number, number] = [15, 23, 42]
): number {
  // Check if browser HTML5 canvas 2D context is properly available
  const isCanvasSupported = (() => {
    try {
      if (typeof window === 'undefined' || typeof document === 'undefined' || !document.createElement) return false;
      // In JSDOM test environments without native canvas, use direct Unicode text rendering
      if (typeof navigator !== 'undefined' && /jsdom/i.test(navigator.userAgent)) return false;
      if (typeof process !== 'undefined' && process.env && process.env.NODE_ENV === 'test') return false;
      const c = document.createElement('canvas');
      return Boolean(c && typeof c.getContext === 'function');
    } catch {
      return false;
    }
  })();

  if (!isCanvasSupported) {
    const lines = doc.splitTextToSize(text, maxWidthMm);
    doc.text(lines, x, y);
    return lines.length * 3.5;
  }

  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      const lines = doc.splitTextToSize(text, maxWidthMm);
      doc.text(lines, x, y);
      return lines.length * 3.5;
    }

    const scale = 2; // High-DPI scale for crisp PDF output
    const fontSizePx = Math.round(fontSizePt * 1.333 * scale);
    const maxPx = Math.max(Math.round((maxWidthMm / 25.4) * 72 * 1.333 * scale), 200);

    ctx.font = `${fontSizePx}px "Noto Sans Malayalam", "Nirmala UI", "Kartika", "Segoe UI", sans-serif`;

    // Accurate word wrapping
    const words = text.split(/\s+/);
    const lines: string[] = [];
    let currentLine = '';

    for (const word of words) {
      const testLine = currentLine ? `${currentLine} ${word}` : word;
      const metrics = ctx.measureText(testLine);
      if (metrics.width > maxPx && currentLine) {
        lines.push(currentLine);
        currentLine = word;
      } else {
        currentLine = testLine;
      }
    }
    if (currentLine) lines.push(currentLine);

    const lineHeightPx = Math.round(fontSizePx * 1.35);
    const canvasHeight = Math.max(lines.length * lineHeightPx + 8, lineHeightPx);

    canvas.width = maxPx;
    canvas.height = canvasHeight;

    ctx.font = `${fontSizePx}px "Noto Sans Malayalam", "Nirmala UI", "Kartika", "Segoe UI", sans-serif`;
    ctx.fillStyle = `rgb(${textColor[0]}, ${textColor[1]}, ${textColor[2]})`;
    ctx.textBaseline = 'top';

    lines.forEach((line, i) => {
      ctx.fillText(line, 0, i * lineHeightPx);
    });

    const imgData = canvas.toDataURL('image/png');
    const imgHeightMm = (canvasHeight / scale / (72 * 1.333)) * 25.4;

    doc.addImage(imgData, 'PNG', x, y - 1, maxWidthMm, imgHeightMm);
    return imgHeightMm;
  } catch {
    const lines = doc.splitTextToSize(text, maxWidthMm);
    doc.text(lines, x, y);
    return lines.length * 3.5;
  }
}

/**
 * Main PDF report generation function consuming real analysis data.
 */
export function generateAudienceIntelligencePdf(
  job: AnalysisJob,
  options: PdfReportOptions = {}
): jsPDF {
  const {
    includeMethodology = true,
    includeComments = true,
    maxComments = 15,
    reportTitle = 'Kollamo.ai Audience Intelligence Executive Report',
    sampleSize = job.total_comments || 250,
    sortMode = 'Most Liked',
    modelName = 'kollamo-muril-5class',
    modelVersion = 'v1',
    processingTime = 'Realtime inference pipeline',
  } = options;

  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  });

  const pageWidth = 210;
  const pageHeight = 297;
  const marginX = 14;
  const contentWidth = pageWidth - marginX * 2;
  let cursorY = 16;

  // Design Tokens & Colors
  const COLOR_PRIMARY: [number, number, number] = [5, 150, 105]; // Emerald-600
  const COLOR_NAVY: [number, number, number] = [15, 23, 42]; // Slate-900
  const COLOR_TEXT: [number, number, number] = [51, 65, 85]; // Slate-700
  const COLOR_MUTED: [number, number, number] = [100, 116, 139]; // Slate-500
  const COLOR_BORDER: [number, number, number] = [226, 232, 240]; // Slate-200
  const COLOR_BG_LIGHT: [number, number, number] = [248, 250, 252]; // Slate-50

  const SENTIMENT_COLORS: Record<string, [number, number, number]> = {
    positive: [16, 185, 129], // Emerald-500
    neutral: [100, 116, 139], // Slate-500
    mixed: [245, 158, 11], // Amber-500
    negative: [239, 68, 68], // Red-500
    unsupported: [113, 113, 122], // Zinc-500
  };

  function checkPageBreak(neededHeight: number) {
    if (cursorY + neededHeight > pageHeight - 18) {
      doc.addPage();
      cursorY = 18;
      drawHeaderRule();
    }
  }

  function drawHeaderRule() {
    doc.setDrawColor(COLOR_PRIMARY[0], COLOR_PRIMARY[1], COLOR_PRIMARY[2]);
    doc.setLineWidth(0.8);
    doc.line(marginX, 12, marginX + contentWidth, 12);
  }

  // --- 1. Top Decorative Brand Bar & Title ---
  doc.setFillColor(COLOR_PRIMARY[0], COLOR_PRIMARY[1], COLOR_PRIMARY[2]);
  doc.rect(0, 0, pageWidth, 5, 'F');

  cursorY = 16;
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10);
  doc.setTextColor(COLOR_PRIMARY[0], COLOR_PRIMARY[1], COLOR_PRIMARY[2]);
  doc.text('KOLLAMO.AI • AUDIENCE INTELLIGENCE PLATFORM', marginX, cursorY);

  cursorY += 7;
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(15);
  doc.setTextColor(COLOR_NAVY[0], COLOR_NAVY[1], COLOR_NAVY[2]);
  doc.text(reportTitle, marginX, cursorY);

  cursorY += 5;
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8.5);
  doc.setTextColor(COLOR_MUTED[0], COLOR_MUTED[1], COLOR_MUTED[2]);
  const genDate = new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC';
  const displayJobId = job.job_id ? `${job.job_id.slice(0, 12)}...` : 'demo-analysis';
  doc.text(`Job ID: ${displayJobId} | Generated: ${genDate} | Status: ${(job.status || 'COMPLETED').toUpperCase()}`, marginX, cursorY);

  cursorY += 5;
  doc.setDrawColor(COLOR_BORDER[0], COLOR_BORDER[1], COLOR_BORDER[2]);
  doc.setLineWidth(0.4);
  doc.line(marginX, cursorY, marginX + contentWidth, cursorY);
  cursorY += 6;

  // --- 2. Video Context & Scope Card ---
  checkPageBreak(32);
  doc.setFillColor(COLOR_BG_LIGHT[0], COLOR_BG_LIGHT[1], COLOR_BG_LIGHT[2]);
  doc.roundedRect(marginX, cursorY, contentWidth, 26, 2, 2, 'F');
  doc.setDrawColor(COLOR_BORDER[0], COLOR_BORDER[1], COLOR_BORDER[2]);
  doc.roundedRect(marginX, cursorY, contentWidth, 26, 2, 2, 'S');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8.5);
  doc.setTextColor(COLOR_NAVY[0], COLOR_NAVY[1], COLOR_NAVY[2]);
  doc.text('Video Title:', marginX + 4, cursorY + 6);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8.5);
  doc.setTextColor(COLOR_TEXT[0], COLOR_TEXT[1], COLOR_TEXT[2]);
  const rawVidTitle = job.video?.title || 'YouTube Video Comment Stream';
  const cleanTitle = rawVidTitle.trim() || 'Malayalam Audience Stream';
  doc.text(doc.splitTextToSize(cleanTitle, 110), marginX + 24, cursorY + 6);

  doc.setFont('helvetica', 'bold');
  doc.text('Channel:', marginX + 4, cursorY + 12);
  doc.setFont('helvetica', 'normal');
  doc.text(job.video?.channel_title || 'Public YouTube Discussion', marginX + 24, cursorY + 12);

  doc.setFont('helvetica', 'bold');
  doc.text('Video ID:', marginX + 4, cursorY + 18);
  doc.setFont('helvetica', 'normal');
  doc.text(job.video?.video_id || (job as { video_id?: string }).video_id || 'N/A', marginX + 24, cursorY + 18);

  const returnedCommentsCount = job.comments ? job.comments.length : (job.processed_comments || 0);

  doc.setFont('helvetica', 'bold');
  doc.text('Comments Analyzed:', marginX + 4, cursorY + 23);
  doc.setFont('helvetica', 'normal');
  doc.text(`${returnedCommentsCount.toLocaleString()} (Limit: ${sampleSize}, Sort: ${sortMode})`, marginX + 40, cursorY + 23);

  // Net Approval in context card
  const posPct = job.summary?.sentiment_percentages?.positive || 0;
  const negPct = job.summary?.sentiment_percentages?.negative || 0;
  const netApproval = +(posPct - negPct).toFixed(1);
  const consensusLabel =
    netApproval >= 60 ? 'Overwhelmingly Positive' :
    netApproval >= 20 ? 'Predominantly Favorable' :
    netApproval >= -20 ? 'Mixed / Divided' : 'Critical / Unfavorable';

  doc.setFont('helvetica', 'bold');
  doc.text('Net Approval Index:', marginX + 115, cursorY + 12);
  doc.setTextColor(
    netApproval >= 0 ? COLOR_PRIMARY[0] : 220,
    netApproval >= 0 ? COLOR_PRIMARY[1] : 38,
    netApproval >= 0 ? COLOR_PRIMARY[2] : 38
  );
  doc.text(`${netApproval >= 0 ? '+' : ''}${netApproval}%`, marginX + 152, cursorY + 12);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(COLOR_MUTED[0], COLOR_MUTED[1], COLOR_MUTED[2]);
  doc.text(`(${consensusLabel})`, marginX + 115, cursorY + 18);

  cursorY += 32;

  // --- 3. Executive Metrics Highlights ---
  checkPageBreak(22);
  const metricBoxWidth = (contentWidth - 9) / 4;
  const dominantSentiment = job.summary?.sentiment_counts
    ? Object.entries(job.summary.sentiment_counts).sort((a, b) => b[1] - a[1])[0]?.[0]?.toUpperCase() || 'POSITIVE'
    : 'POSITIVE';

  const metrics = [
    { label: 'Dominant Sentiment', value: dominantSentiment },
    { label: 'Total Likes Recorded', value: (job.summary?.engagement_metrics?.total_likes || 0).toLocaleString() },
    {
      label: 'Avg Likes / Comment',
      value: ((job.summary?.engagement_metrics?.total_likes || 0) / Math.max(1, returnedCommentsCount || 1)).toFixed(1),
    },
    { label: 'Model Backbone', value: modelName },
  ];

  metrics.forEach((m, idx) => {
    const boxX = marginX + idx * (metricBoxWidth + 3);
    doc.setFillColor(COLOR_BG_LIGHT[0], COLOR_BG_LIGHT[1], COLOR_BG_LIGHT[2]);
    doc.roundedRect(boxX, cursorY, metricBoxWidth, 18, 1.5, 1.5, 'F');
    doc.setDrawColor(COLOR_BORDER[0], COLOR_BORDER[1], COLOR_BORDER[2]);
    doc.roundedRect(boxX, cursorY, metricBoxWidth, 18, 1.5, 1.5, 'S');

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7.5);
    doc.setTextColor(COLOR_MUTED[0], COLOR_MUTED[1], COLOR_MUTED[2]);
    doc.text(m.label, boxX + 3, cursorY + 5);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(9.5);
    doc.setTextColor(COLOR_NAVY[0], COLOR_NAVY[1], COLOR_NAVY[2]);
    doc.text(m.value, boxX + 3, cursorY + 13);
  });

  cursorY += 24;

  // --- 4. 5-Class Sentiment Distribution Table & Proportion Bars ---
  checkPageBreak(48);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(11);
  doc.setTextColor(COLOR_NAVY[0], COLOR_NAVY[1], COLOR_NAVY[2]);
  doc.text('1. Five-Class Sentiment Distribution & Audience Share', marginX, cursorY);
  cursorY += 6;

  const sentimentClasses = ['positive', 'neutral', 'mixed', 'negative', 'unsupported'];
  const counts = job.summary?.sentiment_counts || { positive: 0, neutral: 0, mixed: 0, negative: 0, unsupported: 0 };
  const avgLikesMap = job.summary?.engagement_metrics?.average_likes_per_sentiment || {
    positive: 0, neutral: 0, mixed: 0, negative: 0, unsupported: 0,
  };

  // Safe percentage calculation avoiding division by zero (Section 21)
  const totalCommentsForPct = returnedCommentsCount > 0 ? returnedCommentsCount : 0;
  const pcts: Record<string, number> = {};
  sentimentClasses.forEach((cat) => {
    const count = counts[cat as keyof typeof counts] || 0;
    pcts[cat] = totalCommentsForPct > 0 ? (count / totalCommentsForPct) * 100 : 0.0;
  });

  // Table header row
  doc.setFillColor(COLOR_BORDER[0], COLOR_BORDER[1], COLOR_BORDER[2]);
  doc.rect(marginX, cursorY, contentWidth, 6, 'F');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8);
  doc.setTextColor(COLOR_NAVY[0], COLOR_NAVY[1], COLOR_NAVY[2]);
  doc.text('Sentiment Class', marginX + 4, cursorY + 4.2);
  doc.text('Volume', marginX + 40, cursorY + 4.2);
  doc.text('Share (%)', marginX + 66, cursorY + 4.2);
  doc.text('Proportion Bar', marginX + 96, cursorY + 4.2);
  doc.text('Avg Likes', marginX + 158, cursorY + 4.2);
  cursorY += 6;

  sentimentClasses.forEach((cat) => {
    const count = counts[cat as keyof typeof counts] || 0;
    const pct = pcts[cat] || 0;
    const avgLikes = avgLikesMap[cat as keyof typeof avgLikesMap] || 0;
    const color = SENTIMENT_COLORS[cat] || COLOR_MUTED;

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8);
    doc.setTextColor(color[0], color[1], color[2]);
    doc.text(cat.toUpperCase(), marginX + 4, cursorY + 4.5);

    doc.setFont('helvetica', 'normal');
    doc.setTextColor(COLOR_TEXT[0], COLOR_TEXT[1], COLOR_TEXT[2]);
    doc.text(count.toLocaleString(), marginX + 40, cursorY + 4.5);
    doc.text(`${pct.toFixed(1)}%`, marginX + 66, cursorY + 4.5);

    // Visual proportional share bar
    const barMaxWidth = 55;
    const barWidth = Math.max(1, (pct / 100) * barMaxWidth);
    doc.setFillColor(color[0], color[1], color[2]);
    doc.roundedRect(marginX + 96, cursorY + 1.5, barWidth, 3.5, 0.8, 0.8, 'F');

    doc.text(String(avgLikes), marginX + 158, cursorY + 4.5);

    doc.setDrawColor(COLOR_BORDER[0], COLOR_BORDER[1], COLOR_BORDER[2]);
    doc.setLineWidth(0.2);
    doc.line(marginX, cursorY + 6, marginX + contentWidth, cursorY + 6);
    cursorY += 6;
  });

  cursorY += 8;

  // --- 5. Selected Comments with Malayalam & English Translation Support ---
  if (includeComments) {
    checkPageBreak(30);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(COLOR_NAVY[0], COLOR_NAVY[1], COLOR_NAVY[2]);
    doc.text('2. Community Discourse & English Readability Translations', marginX, cursorY);
    cursorY += 6;

    if (!job.comments || job.comments.length === 0) {
      // Empty state handling (Section 21)
      checkPageBreak(16);
      doc.setFillColor(COLOR_BG_LIGHT[0], COLOR_BG_LIGHT[1], COLOR_BG_LIGHT[2]);
      doc.roundedRect(marginX, cursorY, contentWidth, 14, 1.5, 1.5, 'F');
      doc.setFont('helvetica', 'italic');
      doc.setFontSize(8.5);
      doc.setTextColor(COLOR_MUTED[0], COLOR_MUTED[1], COLOR_MUTED[2]);
      doc.text('No audience comments were returned or available for analysis for this video stream.', marginX + 4, cursorY + 8);
      cursorY += 20;
    } else {
      const sampleComments: CommentItem[] = job.comments.slice(0, maxComments);

      sampleComments.forEach((c, idx) => {
        const containsMalayalam = /[\u0D00-\u0D7F]/.test(c.original_text);
        const transText = c.translated_text
          ? `English Translation: "${c.translated_text}"`
          : 'English Translation: Not required (Already in English)';

        const transLines = doc.splitTextToSize(transText, contentWidth - 8);
        const origHeightEstimate = containsMalayalam ? 8 : (doc.splitTextToSize(`Original: "${c.original_text}"`, contentWidth - 8).length * 3.5);
        const blockHeight = 14 + origHeightEstimate + transLines.length * 3.5;

        checkPageBreak(blockHeight);

        // Container card
        doc.setFillColor(idx % 2 === 0 ? COLOR_BG_LIGHT[0] : 255, idx % 2 === 0 ? COLOR_BG_LIGHT[1] : 255, idx % 2 === 0 ? COLOR_BG_LIGHT[2] : 255);
        doc.roundedRect(marginX, cursorY, contentWidth, blockHeight - 2, 1.5, 1.5, 'F');
        doc.setDrawColor(COLOR_BORDER[0], COLOR_BORDER[1], COLOR_BORDER[2]);
        doc.setLineWidth(0.3);
        doc.roundedRect(marginX, cursorY, contentWidth, blockHeight - 2, 1.5, 1.5, 'S');

        // Card header line: Author, sentiment pill, confidence, likes
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(8);
        doc.setTextColor(COLOR_NAVY[0], COLOR_NAVY[1], COLOR_NAVY[2]);
        doc.text(c.author_display_name || 'Audience Member', marginX + 4, cursorY + 5);

        // Sentiment pill
        const sentColor = SENTIMENT_COLORS[c.sentiment] || COLOR_MUTED;
        doc.setFillColor(sentColor[0], sentColor[1], sentColor[2]);
        doc.roundedRect(marginX + 60, cursorY + 1.8, 22, 4, 1, 1, 'F');
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(6.5);
        doc.setTextColor(255, 255, 255);
        doc.text(c.sentiment.toUpperCase(), marginX + 63, cursorY + 4.6);

        // Meta info
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(7.5);
        doc.setTextColor(COLOR_MUTED[0], COLOR_MUTED[1], COLOR_MUTED[2]);
        doc.text(`Conf: ${(c.confidence * 100).toFixed(1)}% | Likes: ${c.like_count}`, marginX + 88, cursorY + 5);

        let textCursor = cursorY + 9;

        // Render original comment (using Malayalam Unicode helper if needed)
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(7.5);
        doc.setTextColor(COLOR_NAVY[0], COLOR_NAVY[1], COLOR_NAVY[2]);
        doc.text('Original:', marginX + 4, textCursor);

        if (containsMalayalam) {
          const renderedHeight = renderMalayalamTextToPdf(
            doc,
            c.original_text,
            marginX + 16,
            textCursor,
            contentWidth - 20,
            8,
            COLOR_TEXT
          );
          textCursor += Math.max(renderedHeight, 6);
        } else {
          doc.setFont('helvetica', 'normal');
          doc.setFontSize(7.5);
          doc.setTextColor(COLOR_TEXT[0], COLOR_TEXT[1], COLOR_TEXT[2]);
          const origLines = doc.splitTextToSize(`"${c.original_text}"`, contentWidth - 20);
          doc.text(origLines, marginX + 16, textCursor);
          textCursor += origLines.length * 3.5;
        }

        // Render English Translation
        doc.setFont('helvetica', 'italic');
        doc.setFontSize(7.5);
        doc.setTextColor(COLOR_PRIMARY[0], COLOR_PRIMARY[1], COLOR_PRIMARY[2]);
        doc.text(transLines, marginX + 4, textCursor + 1);

        cursorY += blockHeight;
      });

      cursorY += 6;
    }
  }

  // --- 6. Technical Methodology & NLP Model Disclosures (Section 25 & 26) ---
  if (includeMethodology) {
    checkPageBreak(38);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(COLOR_NAVY[0], COLOR_NAVY[1], COLOR_NAVY[2]);
    doc.text('3. Machine Learning Methodology & Architecture', marginX, cursorY);
    cursorY += 6;

    doc.setFillColor(COLOR_BG_LIGHT[0], COLOR_BG_LIGHT[1], COLOR_BG_LIGHT[2]);
    doc.roundedRect(marginX, cursorY, contentWidth, 30, 1.5, 1.5, 'F');
    doc.setDrawColor(COLOR_BORDER[0], COLOR_BORDER[1], COLOR_BORDER[2]);
    doc.roundedRect(marginX, cursorY, contentWidth, 30, 1.5, 1.5, 'S');

    const methodLines = [
      ['Transformer Model:', `${modelName} (${modelVersion})`],
      ['Checkpoint / Weights:', 'google/muril-base-cased fine-tuned for Malayalam-English social discourse'],
      ['Classification Head:', 'Linear projection over 5 discrete classes (Positive, Negative, Neutral, Mixed, Unsupported)'],
      ['Probabilities Label:', 'Model class probabilities (multinomial classification distribution)'],
      ['Translation Engine:', 'Multi-tier colloquial Manglish lexicon + neural translation abstraction layer'],
      ['Telemetry & Runtime:', processingTime],
    ];

    methodLines.forEach(([label, val], idx) => {
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(7.5);
      doc.setTextColor(COLOR_NAVY[0], COLOR_NAVY[1], COLOR_NAVY[2]);
      doc.text(label, marginX + 4, cursorY + 4.5 + idx * 4.6);

      doc.setFont('helvetica', 'normal');
      doc.setTextColor(COLOR_TEXT[0], COLOR_TEXT[1], COLOR_TEXT[2]);
      doc.text(val, marginX + 38, cursorY + 4.5 + idx * 4.6);
    });

    cursorY += 36;
  }

  // --- 7. Academic Disclaimer ---
  checkPageBreak(18);
  doc.setDrawColor(COLOR_BORDER[0], COLOR_BORDER[1], COLOR_BORDER[2]);
  doc.setLineWidth(0.4);
  doc.line(marginX, cursorY, marginX + contentWidth, cursorY);
  cursorY += 4;

  doc.setFont('helvetica', 'italic');
  doc.setFontSize(7);
  doc.setTextColor(COLOR_MUTED[0], COLOR_MUTED[1], COLOR_MUTED[2]);
  const disclaimer =
    'Academic Disclaimer: Kollamo.ai is an MCA academic research project engineered for Malayalam-English sentiment analysis and audience intelligence. Sentiment classifications represent probabilistic model inferences and should not be construed as definitive factual assertions. Predictions may reflect colloquial idioms, sarcasm, or regional slang.';
  const discLines = doc.splitTextToSize(disclaimer, contentWidth);
  doc.text(discLines, marginX, cursorY);

  // --- 8. Running Page Footers across all pages ---
  const totalPages = doc.getNumberOfPages();
  for (let p = 1; p <= totalPages; p++) {
    doc.setPage(p);
    doc.setDrawColor(COLOR_BORDER[0], COLOR_BORDER[1], COLOR_BORDER[2]);
    doc.setLineWidth(0.3);
    doc.line(marginX, pageHeight - 10, marginX + contentWidth, pageHeight - 10);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7.5);
    doc.setTextColor(COLOR_MUTED[0], COLOR_MUTED[1], COLOR_MUTED[2]);
    doc.text('Kollamo.ai — Malayalam-English Sentiment & Audience Intelligence', marginX, pageHeight - 6);
    doc.text(`Page ${p} of ${totalPages}`, marginX + contentWidth - 16, pageHeight - 6);
  }

  return doc;
}

/**
 * Standardized Phase 8 generateAnalysisReport contract consuming AnalysisResult or AnalysisJob.
 */
export function generateAnalysisReport(analysisResult: any, options: PdfReportOptions = {}): jsPDF {
  // Normalize if analysisResult is wrapped
  const job: AnalysisJob = analysisResult?.job_id ? analysisResult : {
    job_id: analysisResult?.video?.video_id || 'analysis-job',
    status: 'completed',
    progress: 1.0,
    processed_comments: analysisResult?.comments?.length || 0,
    total_comments: analysisResult?.comments?.length || 0,
    video: analysisResult?.video,
    summary: analysisResult?.summary,
    comments: analysisResult?.comments || [],
    created_at: new Date().toISOString(),
  };

  return generateAudienceIntelligencePdf(job, options);
}
