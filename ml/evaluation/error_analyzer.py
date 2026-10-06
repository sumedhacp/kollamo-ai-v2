"""Linguistic Error Analysis Engine for Kollamo.ai.

Analyzes model failure modes across 8 core linguistic phenomena:
1. Slang & Colloquialisms
2. Spelling Variation in Manglish
3. Code-Mixing
4. Sarcasm & Irony
5. Negation Particles
6. Emojis
7. Short Comments (< 3 words)
8. Ambiguous / Balanced Comments
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
from ml.data.dataset_loader import ID2LABEL, LABEL2ID, SENTIMENT_LABELS


# Curated diagnostic probe suite specifically targeting the 8 phenomena
DIAGNOSTIC_PROBES = [
    # 1. Slang & Colloquialisms
    {"text": "Ee padam kidilan item aanu, tharumaru aavesham!", "true_label": "positive", "category": "slang"},
    {"text": "Full chali comedy aayirunnu, sahikkan pattiyilla.", "true_label": "negative", "category": "slang"},
    {"text": "Polichu adukki kalanju machane!", "true_label": "positive", "category": "slang"},
    {"text": "Theerumanam aayi, verum oola padam.", "true_label": "negative", "category": "slang"},

    # 2. Spelling Variation in Manglish
    {"text": "Aadipoli cinima must watch!", "true_label": "positive", "category": "spelling_variation"},
    {"text": "Athipoli film, superb acting.", "true_label": "positive", "category": "spelling_variation"},
    {"text": "Adypoli experience aayirunnu.", "true_label": "positive", "category": "spelling_variation"},

    # 3. Code-Mixing
    {"text": "First half super pace aayirunnu but second half full drag.", "true_label": "mixed", "category": "code_mixing"},
    {"text": "Mass action scenes nannayi eduthittundu but logic zero.", "true_label": "mixed", "category": "code_mixing"},
    {"text": "Lead actor killed it pakshe screenplay utterly disappointed.", "true_label": "mixed", "category": "code_mixing"},

    # 4. Sarcasm & Irony
    {"text": "Aaha enthoru nalla padam, urangan nallathaanu!", "true_label": "negative", "category": "sarcasm"},
    {"text": "Oscar kodukkendi varum ee mahaa tharangalkku.", "true_label": "negative", "category": "sarcasm"},

    # 5. Negation Particles
    {"text": "Oru nalla scene polum ithil illa.", "true_label": "negative", "category": "negation"},
    {"text": "Kandu theerkkan pattathilla, valare mosham.", "true_label": "negative", "category": "negation"},
    {"text": "Aarum pokathirikkan sramikkuka.", "true_label": "negative", "category": "negation"},

    # 6. Emojis
    {"text": "Theatre explosion 🔥🔥🔥 best movie ever ❤️", "true_label": "positive", "category": "emojis"},
    {"text": "Valare bore aayirunnu 🤮👎🤮", "true_label": "negative", "category": "emojis"},
    {"text": "Songs kollam pakshe climax 😐", "true_label": "mixed", "category": "emojis"},

    # 7. Short Comments
    {"text": "Mass", "true_label": "positive", "category": "short_comments"},
    {"text": "Chali", "true_label": "negative", "category": "short_comments"},
    {"text": "Kollam", "true_label": "positive", "category": "short_comments"},
    {"text": "Disaster", "true_label": "negative", "category": "short_comments"},

    # 8. Ambiguous / Nuanced Comments
    {"text": "Oru thavana kaanam, valiya sambhavam onnum alla pakshe kuzhappamilla.", "true_label": "mixed", "category": "ambiguous"},
    {"text": "Average padam, time passinu kollam.", "true_label": "neutral", "category": "ambiguous"},
]


def run_error_analysis(predict_fn) -> Dict[str, Any]:
    """Runs prediction function across diagnostic probes and computes category-wise accuracy.

    Args:
        predict_fn: Callable taking a string or list of strings and returning list of predicted label strings.
    """
    results = []
    category_stats = {}

    for item in DIAGNOSTIC_PROBES:
        text = item["text"]
        true_label = item["true_label"]
        category = item["category"]

        pred = predict_fn([text])[0]
        if isinstance(pred, int):
            pred_label = ID2LABEL[pred]
        else:
            pred_label = str(pred).lower()

        is_correct = (pred_label == true_label)

        results.append({
            "text": text,
            "category": category,
            "true_label": true_label,
            "predicted_label": pred_label,
            "is_correct": is_correct,
        })

        if category not in category_stats:
            category_stats[category] = {"total": 0, "correct": 0}
        category_stats[category]["total"] += 1
        if is_correct:
            category_stats[category]["correct"] += 1

    summary = {}
    for cat, stats in category_stats.items():
        summary[cat] = {
            "total_tested": stats["total"],
            "correct": stats["correct"],
            "accuracy": round(stats["correct"] / stats["total"], 4),
            "error_rate": round(1.0 - (stats["correct"] / stats["total"]), 4),
        }

    overall_correct = sum(1 for r in results if r["is_correct"])
    overall_total = len(results)

    analysis_report = {
        "overall_diagnostic_accuracy": round(overall_correct / overall_total, 4),
        "total_probes_evaluated": overall_total,
        "category_breakdown": summary,
        "detailed_probe_results": results,
    }

    return analysis_report
