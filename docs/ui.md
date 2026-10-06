# UI/UX Specification & Design System — Kollamo.ai

## 1. Aesthetic & Experience Principles

Kollamo.ai represents a modern, high-trust SaaS intelligence product.
- **Tone**: Clean, focused, analytical, accessible.
- **Cognitive Load**: Low cognitive friction; high readability; structured data hierarchy.
- **Anti-patterns to avoid**: Excessive gradients, loud neon styling, heavy glassmorphism, gratuitous animations, tiny text, and crypto/gaming visuals.

---

## 2. Color System & Semantic Tokens

### Sentiment Semantic Colors
| Sentiment | Color Family | Hex (Light / Dark) | Semantic Purpose |
| :--- | :--- | :--- | :--- |
| **Positive** | Emerald / Green | `#10B981` / `#059669` | Praise, satisfaction, high approval |
| **Negative** | Rose / Red | `#EF4444` / `#DC2626` | Criticism, disapproval, frustration |
| **Neutral** | Slate / Gray | `#64748B` / `#475569` | Objective, factual, inquiries |
| **Mixed** | Amber / Orange | `#F59E0B` / `#D97706` | Nuanced, co-occurring praise & critique |
| **Unsupported** | Zinc / Muted | `#71717A` / `#52525B` | Unintelligible noise, unsupported characters |

*Rule*: Never use color alone to convey sentiment. Always couple colors with descriptive text labels and semantic icons.

---

## 3. Four Essential UI States

Every view, card, chart, and table must implement four distinct states:
1. **Loading State**: Accessible skeleton screens matching final layout dimensions. No generic blank spinners.
2. **Empty State**: Clear contextual iconography, explanatory copy, and explicit action buttons.
3. **Success / Data State**: Polished tables, interactive charts, and metric badge cards.
4. **Error State**: Descriptive error explanation, status code where relevant, and a clear "Retry" action.

---

## 4. Primary Application Routes

- `/`: Landing page introducing the code-mixed sentiment problem, features, and non-technical workflow.
- `/sandbox`: Single-comment testing sandbox with script detection, character counter, and confidence distribution breakdown.
- `/analyze`: YouTube ingestion form supporting sample sizes (50, 100, 250, 500, ALL) and sort modes.
- `/analysis/:jobId`: Live job tracker transitioning seamlessly into the Audience Intelligence Dashboard with filters, charts, and PDF export.
