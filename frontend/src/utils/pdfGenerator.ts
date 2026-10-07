/**
 * Client-Side PDF Report Generator for Kollamo.ai.
 *
 * Compiles a comprehensive, multi-page, publication-quality academic
 * Audience Intelligence Report using jsPDF.
 */

import { jsPDF } from 'jspdf';
import { AnalysisJob, CommentItem } from '@/types';

export interface PdfReportOptions {
  includeMethodology?: boolean;
  includeComments?: boolean;
  maxComments?: number;
  reportTitle?: string;
}

export function generateAudienceIntelligencePdf(
  job: AnalysisJob,
  options: PdfReportOptions = {}
): jsPDF {
  const {
    includeMethodology = true,
    includeComments = true,
    maxComments = 10,
    reportTitle = 'Kollamo.ai Audience Intelligence Executive Report',
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

  // Colors
  const COLOR_PRIMARY = [5, 150, 105]; // Emerald-600
  const COLOR_NAVY = [15, 23, 42]; // Slate-900
  const COLOR_TEXT = [51, 65, 85]; // Slate-700
  const COLOR_MUTED = [100, 116, 139]; // Slate-500
  const COLOR_BORDER = [226, 232, 240]; // Slate-200
  const COLOR_BG_LIGHT = [248, 250, 252]; // Slate-50

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
  doc.text('KOLLAMO.AI &bull; ACADEMIC RESEARCH PLATFORM', marginX, cursorY);

  cursorY += 7;
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(16);
  doc.setTextColor(COLOR_NAVY[0], COLOR_NAVY[1], COLOR_NAVY[2]);
  doc.text(reportTitle, marginX, cursorY);

  cursorY += 5;
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  doc.setTextColor(COLOR_MUTED[0], COLOR_MUTED[1], COLOR_MUTED[2]);
  const genDate = new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC';
  doc.text(`Job ID: ${job.job_id.slice(0, 12)}... | Generated: ${genDate} | Status: ${job.status.toUpperCase()}`, marginX, cursorY);

  cursorY += 5;
  doc.setDrawColor(COLOR_BORDER[0], COLOR_BORDER[1], COLOR_BORDER[2]);
  doc.setLineWidth(0.4);
  doc.line(marginX, cursorY, marginX + contentWidth, cursorY);
  cursorY += 6;

  // --- 2. Video Context & Scope Card ---
  checkPageBreak(30);
  doc.setFillColor(COLOR_BG_LIGHT[0], COLOR_BG_LIGHT[1], COLOR_BG_LIGHT[2]);
  doc.roundedRect(marginX, cursorY, contentWidth, 24, 2, 2, 'F');
  doc.setDrawColor(COLOR_BORDER[0], COLOR_BORDER[1], COLOR_BORDER[2]);
  doc.roundedRect(marginX, cursorY, contentWidth, 24, 2, 2, 'S');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9);
  doc.setTextColor(COLOR_NAVY[0], COLOR_NAVY[1], COLOR_NAVY[2]);
  doc.text('Analyzed Subject:', marginX + 4, cursorY + 6);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  doc.setTextColor(COLOR_TEXT[0], COLOR_TEXT[1], COLOR_TEXT[2]);
  const videoTitle = job.video?.title || 'YouTube Comment Stream Ingestion';
  const cleanTitle = videoTitle.replace(/[^\x00-\x7F]/g, '').trim() || 'Malayalam Audience Stream';
  doc.text(doc.splitTextToSize(cleanTitle, 120), marginX + 35, cursorY + 6);

  doc.setFont('helvetica', 'bold');
  doc.text('Channel:', marginX + 4, cursorY + 12);
  doc.setFont('helvetica', 'normal');
  doc.text(job.video?.channel_title || 'Public YouTube Discussion', marginX + 22, cursorY + 12);

  doc.setFont('helvetica', 'bold');
  doc.text('Total Comments Analyzed:', marginX + 4, cursorY + 18);
  doc.setFont('helvetica', 'normal');
  doc.text(`${(job.processed_comments || job.total_comments || 0).toLocaleString()} comments`, marginX + 48, cursorY + 18);

  // Net Approval in context card
  const posPct = job.summary?.sentiment_percentages?.positive || 0;
  const negPct = job.summary?.sentiment_percentages?.negative || 0;
  const netApproval = +(posPct - negPct).toFixed(1);
  const consensusLabel =
    netApproval >= 60 ? 'Overwhelmingly Positive' :
    netApproval >= 20 ? 'Predominantly Favorable' :
    netApproval >= -20 ? 'Mixed / Divided' : 'Critical / Unfavorable';

  doc.setFont('helvetica', 'bold');
  doc.text('Net Sentiment Index:', marginX + 115, cursorY + 12);
  doc.setTextColor(netApproval >= 0 ? COLOR_PRIMARY[0] : 220, netApproval >= 0 ? COLOR_PRIMARY[1] : 38, netApproval >= 0 ? COLOR_PRIMARY[2] : 38);
  doc.text(`${netApproval >= 0 ? '+' : ''}${netApproval}%`, marginX + 152, cursorY + 12);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(COLOR_MUTED[0], COLOR_MUTED[1], COLOR_MUTED[2]);
  doc.text(`(${consensusLabel})`, marginX + 115, cursorY + 18);

  cursorY += 30;

  // --- 3. Executive Metrics Highlights ---
  checkPageBreak(22);
  const metricBoxWidth = (contentWidth - 9) / 4;
  const metrics = [
    { label: 'Dominant Sentiment', value: (job.summary ? Object.entries(job.summary.sentiment_counts).sort((a,b) => b[1] - a[1])[0]?.[0]?.toUpperCase() : 'POSITIVE') || 'POSITIVE' },
    { label: 'Total Community Likes', value: (job.summary?.engagement_metrics?.total_likes || 0).toLocaleString() },
    { label: 'Average Likes / Comment', value: ((job.summary?.engagement_metrics?.total_likes || 0) / Math.max(1, job.processed_comments || 1)).toFixed(1) },
    { label: 'Linguistic Classes', value: 'Malayalam / Manglish' },
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
    doc.setFontSize(10.5);
    doc.setTextColor(COLOR_NAVY[0], COLOR_NAVY[1], COLOR_NAVY[2]);
    doc.text(m.value, boxX + 3, cursorY + 13);
  });

  cursorY += 24;

  // --- 4. 5-Class Sentiment Distribution & Visual Share Bars ---
  checkPageBreak(45);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(11);
  doc.setTextColor(COLOR_NAVY[0], COLOR_NAVY[1], COLOR_NAVY[2]);
  doc.text('1. Five-Class Sentiment Distribution & Audience Share', marginX, cursorY);
  cursorY += 6;

  const sentimentClasses = ['positive', 'neutral', 'mixed', 'negative', 'unsupported'];
  const counts = job.summary?.sentiment_counts || { positive: 0, neutral: 0, mixed: 0, negative: 0, unsupported: 0 };
  const pcts = job.summary?.sentiment_percentages || { positive: 0, neutral: 0, mixed: 0, negative: 0, unsupported: 0 };
  const avgLikesMap = job.summary?.engagement_metrics?.average_likes_per_sentiment || {
    positive: 0, neutral: 0, mixed: 0, negative: 0, unsupported: 0,
  };

  // Header row
  doc.setFillColor(COLOR_BORDER[0], COLOR_BORDER[1], COLOR_BORDER[2]);
  doc.rect(marginX, cursorY, contentWidth, 6, 'F');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8);
  doc.setTextColor(COLOR_NAVY[0], COLOR_NAVY[1], COLOR_NAVY[2]);
  doc.text('Category', marginX + 4, cursorY + 4.2);
  doc.text('Volume', marginX + 36, cursorY + 4.2);
  doc.text('Share (%)', marginX + 60, cursorY + 4.2);
  doc.text('Visual Proportion Bar', marginX + 90, cursorY + 4.2);
  doc.text('Avg Likes', marginX + 155, cursorY + 4.2);
  cursorY += 6;

  sentimentClasses.forEach((cat) => {
    const count = counts[cat as keyof typeof counts] || 0;
    const pct = pcts[cat as keyof typeof pcts] || 0;
    const avgLikes = avgLikesMap[cat as keyof typeof avgLikesMap] || 0;
    const color = SENTIMENT_COLORS[cat] || COLOR_MUTED;

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8);
    doc.setTextColor(color[0], color[1], color[2]);
    doc.text(cat.toUpperCase(), marginX + 4, cursorY + 4.5);

    doc.setFont('helvetica', 'normal');
    doc.setTextColor(COLOR_TEXT[0], COLOR_TEXT[1], COLOR_TEXT[2]);
    doc.text(count.toLocaleString(), marginX + 36, cursorY + 4.5);
    doc.text(`${pct.toFixed(1)}%`, marginX + 60, cursorY + 4.5);

    // Visual bar
    const barMaxWidth = 55;
    const barWidth = Math.max(1, (pct / 100) * barMaxWidth);
    doc.setFillColor(color[0], color[1], color[2]);
    doc.roundedRect(marginX + 90, cursorY + 1.5, barWidth, 3.5, 0.8, 0.8, 'F');

    doc.text(String(avgLikes), marginX + 155, cursorY + 4.5);

    doc.setDrawColor(COLOR_BORDER[0], COLOR_BORDER[1], COLOR_BORDER[2]);
    doc.setLineWidth(0.2);
    doc.line(marginX, cursorY + 6, marginX + contentWidth, cursorY + 6);
    cursorY += 6;
  });

  cursorY += 8;

  // --- 5. Selected Exemplary Comments Table ---
  if (includeComments && job.comments && job.comments.length > 0) {
    checkPageBreak(30);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(COLOR_NAVY[0], COLOR_NAVY[1], COLOR_NAVY[2]);
    doc.text('2. Exemplary Community Discourse & English Translations', marginX, cursorY);
    cursorY += 6;

    const sampleComments: CommentItem[] = job.comments.slice(0, maxComments);

    sampleComments.forEach((c, idx) => {
      // Calculate needed height for this comment block
      const cleanOrig = c.original_text.replace(/[^\x00-\x7F]/g, '').trim() || '[Regional Malayalam Script Comment]';
      const origLines = doc.splitTextToSize(`Original: "${cleanOrig}"`, contentWidth - 8);
      const transText = c.translated_text ? `Translation: "${c.translated_text}"` : 'Translation: None required / unavailable';
      const transLines = doc.splitTextToSize(transText, contentWidth - 8);
      const blockHeight = 12 + origLines.length * 3.5 + transLines.length * 3.5;

      checkPageBreak(blockHeight);

      // Card container
      doc.setFillColor(idx % 2 === 0 ? COLOR_BG_LIGHT[0] : 255, idx % 2 === 0 ? COLOR_BG_LIGHT[1] : 255, idx % 2 === 0 ? COLOR_BG_LIGHT[2] : 255);
      doc.roundedRect(marginX, cursorY, contentWidth, blockHeight - 2, 1.5, 1.5, 'F');
      doc.setDrawColor(COLOR_BORDER[0], COLOR_BORDER[1], COLOR_BORDER[2]);
      doc.setLineWidth(0.3);
      doc.roundedRect(marginX, cursorY, contentWidth, blockHeight - 2, 1.5, 1.5, 'S');

      // Top line of card: author, sentiment badge, confidence, likes
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

      // Meta
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(7.5);
      doc.setTextColor(COLOR_MUTED[0], COLOR_MUTED[1], COLOR_MUTED[2]);
      doc.text(`Conf: ${(c.confidence * 100).toFixed(1)}% | Likes: ${c.like_count}`, marginX + 88, cursorY + 5);

      let textCursor = cursorY + 9;
      // Original text
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(7.5);
      doc.setTextColor(COLOR_TEXT[0], COLOR_TEXT[1], COLOR_TEXT[2]);
      doc.text(origLines, marginX + 4, textCursor);
      textCursor += origLines.length * 3.5;

      // Translated text
      doc.setFont('helvetica', 'italic');
      doc.setTextColor(COLOR_PRIMARY[0], COLOR_PRIMARY[1], COLOR_PRIMARY[2]);
      doc.text(transLines, marginX + 4, textCursor);

      cursorY += blockHeight;
    });

    cursorY += 6;
  }

  // --- 6. Technical Methodology & NLP Model Disclosures ---
  if (includeMethodology) {
    checkPageBreak(35);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(COLOR_NAVY[0], COLOR_NAVY[1], COLOR_NAVY[2]);
    doc.text('3. Machine Learning Methodology & Architecture', marginX, cursorY);
    cursorY += 6;

    doc.setFillColor(COLOR_BG_LIGHT[0], COLOR_BG_LIGHT[1], COLOR_BG_LIGHT[2]);
    doc.roundedRect(marginX, cursorY, contentWidth, 26, 1.5, 1.5, 'F');
    doc.setDrawColor(COLOR_BORDER[0], COLOR_BORDER[1], COLOR_BORDER[2]);
    doc.roundedRect(marginX, cursorY, contentWidth, 26, 1.5, 1.5, 'S');

    const methodLines = [
      ['Transformer Backbone:', 'Google MuRIL (Multilingual Representations for Indian Languages)'],
      ['Checkpoint / Weights:', 'google/muril-base-cased fine-tuned for Malayalam-English social discourse'],
      ['Classification Head:', 'Linear projection over 5 discrete classes (Positive, Negative, Neutral, Mixed, Unsupported)'],
      ['Translation Engine:', 'Multi-tier colloquial Manglish lexicon + neural translation abstraction layer'],
    ];

    methodLines.forEach(([label, val], idx) => {
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(7.5);
      doc.setTextColor(COLOR_NAVY[0], COLOR_NAVY[1], COLOR_NAVY[2]);
      doc.text(label, marginX + 4, cursorY + 5 + idx * 5.2);

      doc.setFont('helvetica', 'normal');
      doc.setTextColor(COLOR_TEXT[0], COLOR_TEXT[1], COLOR_TEXT[2]);
      doc.text(val, marginX + 40, cursorY + 5 + idx * 5.2);
    });

    cursorY += 32;
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
