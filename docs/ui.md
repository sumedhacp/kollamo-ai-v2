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
- `/dashboard`: Audience Intelligence Dashboard skeleton with sentiment breakdowns, charts, and comment table.

---

## 5. Phase 1 Component Library Implementation

The frontend architecture includes 12 modular accessible primitives located in `frontend/src/components/ui/`:
1. `Button`: Primary, secondary, outline, ghost, and danger variants with built-in loading spinners.
2. `Input`: Accessible text inputs with error state handling and left/right icon support.
3. `Textarea`: Resizable multi-line inputs with helper and validation text.
4. `Card`: Structured container primitives (`CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`).
5. `Badge` & `SentimentBadge`: Standard pill tags and dedicated semantic sentiment badges with accessible icons for all 5 sentiment classes.
6. `Alert`: Semantic alert notifications (info, success, warning, error) with distinct iconography.
7. `Modal`: Accessible dialogs with backdrop blur, ESC key dismiss, and focus confinement.
8. `Table`: Responsive tabular views (`TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell`).
9. `Tabs`: Multi-view navigation toggles with count chips and active states.
10. `Skeleton`: Pulse animation placeholders matching production layouts.
11. `Progress`: Accessible progress bars with real-time percentage indicators.
12. `EmptyState`: Contextual illustration and call-to-action wrapper for zero-data views.

