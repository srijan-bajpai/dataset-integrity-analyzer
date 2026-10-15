"""Standalone, zero-dependency HTML report generator (REQ-89, REQ-90, REQ-91).

This version prioritises readability for non-technical stakeholders by adding
plain-language explainers beneath every piece of jargon, while keeping the
full technical detail available for data engineers.
"""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Plain-language explainers for every dimension and metric
# ---------------------------------------------------------------------------

_DIMENSION_ELI5: dict[str, str] = {
    "Balance": (
        "Are the categories roughly equal in size? If one category has "
        "way more pictures than another, the AI might ignore the smaller one."
    ),
    "Fairness": (
        "Does the dataset represent different groups of people fairly? "
        "If some groups are missing or under-represented, the AI could "
        "perform worse for those groups."
    ),
    "Quality": (
        "Are the images clear and usable? Blurry, too-dark, or corrupted "
        "images can confuse the AI during training."
    ),
    "Uniqueness": (
        "Are there duplicate or near-identical images? Copies waste "
        "resources and can trick the AI into memorising instead of learning."
    ),
    "Diversity": (
        "Do the images cover a wide variety of real-world scenarios? "
        "If all pictures look the same, the AI won't generalise well to "
        "new situations."
    ),
    "Label Integrity": (
        "Are the labels (tags) on each image correct? Wrong labels are "
        "like a teacher giving wrong answers — the AI learns the wrong thing."
    ),
}

_VERDICT_ELI5: dict[str, str] = {
    "Production Ready": (
        "Great news! This dataset looks solid and is ready to use for "
        "training an AI model."
    ),
    "Acceptable": (
        "The dataset is usable, but there are some areas that could "
        "be improved. Consider addressing the recommendations below."
    ),
    "Needs Remediation": (
        "There are noticeable problems that should be fixed before "
        "training a reliable AI model. See the recommendations below."
    ),
    "Critical / Not Usable": (
        "Serious issues were found. Using this dataset as-is would likely "
        "produce an unreliable AI model. Please fix the critical items first."
    ),
    "Not Ready": (
        "A critical safety check failed (e.g. data leaking between "
        "train and test sets, or a dimension scored dangerously low). "
        "This must be resolved before any model training."
    ),
    "Insufficient Coverage": (
        "We couldn't evaluate enough dimensions to give a confident score. "
        "More data or metadata may be needed."
    ),
    "Unassessed": (
        "The dataset hasn't been fully evaluated yet."
    ),
}

_METRIC_ELI5: dict[str, str] = {
    "IR": "Imbalance Ratio — how many times bigger the largest category is compared to the smallest",
    "Shannon H": "Entropy — a number between 0 and 1 that measures how evenly images are spread across categories (1 = perfectly even)",
    "Defects": "Percentage of images that have quality problems like blur or bad lighting",
    "Corrupt": "Number of image files that couldn't be opened at all",
    "Redundancy": "Fraction of images that are copies or near-copies of other images",
    "Cross-split": "Duplicate images that appear in both the training set AND the test set — a serious problem",
    "Cluster entropy": "How visually varied the images are (1 = very diverse, 0 = all look the same)",
    "Prunable": "Images so visually similar to others in their group that removing them wouldn't lose information",
    "Noise rate": "Estimated percentage of images whose labels might be wrong",
    "Suspected": "Number of images where our analysis disagrees with the assigned label",
    "Worst target gap": "Biggest difference between the desired representation of a group and what's actually in the dataset",
}

_PRIORITY_ELI5: dict[str, str] = {
    "Critical": "🚨 Must fix — this is a deal-breaker",
    "High": "⚠️ Strongly recommended — will noticeably improve results",
    "Medium": "📋 Worth doing — improves quality but not urgent",
    "Low": "💡 Nice to have — a small optimisation",
    "Info": "ℹ️ For your information — no action needed",
}

_EFFORT_ELI5: dict[str, str] = {
    "Low": "Quick fix — can be done in minutes with a script",
    "Medium": "Some work — may take a few hours of human review",
    "High": "Significant effort — may require collecting new data",
}


def _score_emoji(score: float | None) -> str:
    """Return an emoji that matches the score band."""
    if score is None:
        return "❓"
    if score >= 85:
        return "🟢"
    if score >= 70:
        return "🟡"
    if score >= 40:
        return "🟠"
    return "🔴"


def _verdict_color_class(verdict: str) -> str:
    v = verdict.lower()
    if "ready" in v and "not" not in v:
        return "green"
    if "acceptable" in v:
        return "amber"
    return "red"


def render_html_report(report: dict[str, Any]) -> str:
    """
    Renders a fully self-contained HTML Dataset Health Report with zero external CDN dependencies.
    Contains:
    1. Executive Summary with AI Readiness Score gauge and verdict (REQ-89.1)
    2. Dataset Overview (REQ-89.2)
    3. Unified Summary Table across all 6 dimensions (REQ-90)
    4. Critical Issues (REQ-89.3)
    5. Cross-Dimensional Confound Findings (REQ-89.4, REQ-62)
    6. Per-Dimension Findings (REQ-89.5)
    7. Bias Impact Prediction (REQ-89.6)
    8. Prioritised, Cost-Aware Recommendations (REQ-89.7, REQ-83)
    9. Actionable Remediation Manifest (REQ-86)
    10. Methodology & Reproducibility Appendix (REQ-89.8)
    """
    results = report.get("results", {})
    readiness = results.get("readiness", {})
    dist = results.get("distribution", {})
    quality = results.get("quality", {})
    duplicates = results.get("duplicates", {})
    diversity = results.get("diversity", {})
    labels = results.get("labels", {})
    fairness = results.get("fairness", {})
    confounds = results.get("confounds", {})
    recs = results.get("recommendations", [])
    manifest = report.get("remediation_manifest", [])

    score = readiness.get("overall_score")
    verdict = readiness.get("verdict") or "Unassessed"
    coverage = readiness.get("coverage_pct", 0.0)

    # Score color band: Red < 40 <= Amber < 70 <= Green
    if score is not None:
        if score < 40:
            score_color = "#ef4444"
            badge_bg = "rgba(239, 68, 68, 0.15)"
            badge_border = "#ef4444"
        elif score < 70:
            score_color = "#f59e0b"
            badge_bg = "rgba(245, 158, 11, 0.15)"
            badge_border = "#f59e0b"
        else:
            score_color = "#10b981"
            badge_bg = "rgba(16, 185, 129, 0.15)"
            badge_border = "#10b981"
    else:
        score_color = "#6b7280"
        badge_bg = "rgba(107, 114, 128, 0.15)"
        badge_border = "#6b7280"

    sub_scores = readiness.get("sub_scores", {})
    weights = readiness.get("weights", {})

    # Build dimension table rows (REQ-90)
    dim_defs = [
        ("Balance", sub_scores.get("Balance"), weights.get("Balance", 0.20),
         f"IR = {dist.get('imbalance_ratio', 'N/A')}:1, Shannon H = {dist.get('normalized_shannon_entropy', 'N/A')}",
         "Balanced" if (dist.get('imbalance_ratio') or 99) <= 1.5 else "Imbalanced"),
        ("Fairness", sub_scores.get("Fairness"), weights.get("Fairness", 0.20),
         f"Worst target gap = {fairness.get('worst_absolute_target_gap', 'None')}",
         "Acceptable" if (fairness.get('worst_absolute_target_gap') or 0) <= 0.10 else "Review"),
        ("Quality", sub_scores.get("Quality"), weights.get("Quality", 0.15),
         f"Defects = {quality.get('defect_rate_pct', 'N/A')}%, Corrupt = {quality.get('invalid_image_count', 0)}",
         "Clean" if (quality.get('defect_rate_pct') or 0) < 5.0 else "Needs Review"),
        ("Uniqueness", sub_scores.get("Uniqueness"), weights.get("Uniqueness", 0.15),
         f"Redundancy = {duplicates.get('redundancy_ratio', 0.0):.1%}, Cross-split = {duplicates.get('cross_split_duplicate_groups', 0)}",
         "Leakage Detected" if duplicates.get('cross_split_duplicate_groups', 0) > 0 else "Unique" if duplicates.get('near_duplicate_count', 0) == 0 else "Redundant"),
        ("Diversity", sub_scores.get("Diversity"), weights.get("Diversity", 0.15),
         f"Cluster entropy = {diversity.get('cluster_entropy', 'N/A')}, Prunable = {diversity.get('total_prunable_samples', 0)}",
         "Adequate" if (diversity.get('cluster_entropy') or 0) >= 0.7 else "Narrow"),
        ("Label Integrity", sub_scores.get("Label Integrity"), weights.get("Label Integrity", 0.15),
         f"Noise rate = {labels.get('label_noise_rate_pct', 'N/A')}%, Suspected = {labels.get('suspected_count', 0)}",
         "Reliable" if (labels.get('label_noise_rate_pct') or 0) <= 2.0 else "Review"),
    ]

    table_rows_html = ""
    for name, s_val, w_val, raw_m, v_str in dim_defs:
        s_display = f"{s_val:.1f}" if s_val is not None else '<span class="text-muted">Not Assessed</span>'
        bar_w = max(0, min(100, s_val)) if s_val is not None else 0
        emoji = _score_emoji(s_val)

        # Build ELI5 explainer for the raw metrics in this row
        eli5_bits = []
        for key, explanation in _METRIC_ELI5.items():
            if key.lower() in raw_m.lower():
                eli5_bits.append(explanation)
        metric_eli5 = "; ".join(eli5_bits) if eli5_bits else ""

        dim_eli5 = _DIMENSION_ELI5.get(name, "")

        table_rows_html += f"""
        <tr>
            <td>
                <div style="font-weight: 600;">{emoji} {html.escape(name)}</div>
                <div class="eli5-hint">{html.escape(dim_eli5)}</div>
            </td>
            <td>
                <div style="font-family: monospace; font-size: 0.9em;">{html.escape(raw_m)}</div>
                <div class="eli5-hint">{html.escape(metric_eli5)}</div>
            </td>
            <td>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="flex: 1; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden;">
                        <div style="width: {bar_w}%; height: 100%; background: {score_color};"></div>
                    </div>
                    <span style="font-weight: 600; min-width: 38px;">{s_display}</span>
                </div>
            </td>
            <td>{w_val:.0%}</td>
            <td><span class="tag">{html.escape(v_str)}</span></td>
        </tr>
        """

    # Recommendations HTML
    recs_html = ""
    for r in recs:
        do_first_badge = '<span class="badge-do-first">🎯 Do This First</span>' if r.get("do_first") else ""
        gain_text = f"+{r.get('projected_score_gain', 0):.1f} pts" if r.get('projected_score_gain') else "N/A"

        priority_key = r.get('priority', 'Info')
        priority_eli5 = _PRIORITY_ELI5.get(priority_key, "")
        effort_eli5 = _EFFORT_ELI5.get(r.get('estimated_effort', 'Medium'), "")

        # Plain-language action summary (from engine or fallback)
        plain_action = r.get("plain_language_action") or r.get("action", "")
        plain_rationale = r.get("plain_language_rationale") or r.get("rationale", "")

        recs_html += f"""
        <div class="card recommendation-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; flex-wrap: wrap; gap: 8px;">
                <div>
                    {do_first_badge}
                    <span class="tag tag-{priority_key.lower()}">{html.escape(priority_key)}</span>
                    <strong style="font-size: 1.1em; margin-left: 6px;">{html.escape(r.get('category', 'General'))}</strong>
                </div>
                <div style="text-align: right; font-size: 0.85em;">
                    <div>Est. Effort: <strong>{html.escape(r.get('estimated_effort', 'Medium'))}</strong></div>
                    <div class="eli5-hint" style="margin-top: 2px;">{html.escape(effort_eli5)}</div>
                    <div style="color: #10b981; font-weight: 600; margin-top: 4px;">Projected Gain: {gain_text}</div>
                    <div class="eli5-hint">How much the overall score would improve if this is fixed</div>
                </div>
            </div>

            <div class="what-we-found">
                <div class="what-we-found-label">🔍 What we found</div>
                {html.escape(str(r.get('defect', '')))}
            </div>

            <div class="what-to-do">
                <div class="what-to-do-label">✅ What to do about it</div>
                {html.escape(str(plain_action))}
            </div>

            <div style="margin-top: 8px;">
                <div class="why-label">💡 Why this matters</div>
                <div style="font-size: 0.92em; color: #4b5563;">{html.escape(str(plain_rationale))}</div>
            </div>

            {f'<div class="trade-off-box">⚡ <strong>Heads up:</strong> {html.escape(str(r.get("trade_off_risk")))}</div>' if r.get("trade_off_risk") else ''}
        </div>
        """

    # Confounds HTML
    confounds_list = confounds.get("detected_confounds", [])
    if confounds_list:
        confounds_html = ""
        for c in confounds_list:
            confounds_html += f"""
            <div class="card confound-card">
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px; flex-wrap: wrap; gap: 6px;">
                    <strong style="color: #b91c1c;">⚠️ {html.escape(c.get('type', 'Confound'))}</strong>
                    <span class="tag tag-warning">Effect: {c.get('effect_size_epsilon_squared') or c.get('effect_size') or 'Significant'}</span>
                </div>
                <div style="font-size: 0.95em; margin-bottom: 4px;">{html.escape(c.get('description', ''))}</div>
                <div class="eli5-box">
                    <strong>In plain English:</strong> {html.escape(c.get('downstream_consequence', 'This could cause the AI to learn the wrong patterns, leading to unfair or inaccurate results.'))}
                </div>
            </div>
            """
    else:
        confounds_html = """<div class='card' style='color: #059669; display: flex; align-items: center; gap: 10px;'>
            <span style="font-size: 1.5em;">✅</span>
            <div>
                <strong>No hidden interactions found</strong>
                <div class="eli5-hint">We checked whether problems in one area (like image quality) unfairly affect specific categories. Everything looks clean.</div>
            </div>
        </div>"""

    # Absent confounds report (REQ-61)
    absent = confounds.get("absent_confounds", [])
    absent_html = ""
    if absent:
        friendly_names = [html.escape(a) for a in absent]
        absent_html = f"""<div class="eli5-box" style="margin-top: 10px;">
            <strong>Things we checked and confirmed are fine:</strong> {', '.join(friendly_names)}
            <div class="eli5-hint">These are potential problems we specifically tested for and ruled out.</div>
        </div>"""

    # Verdict ELI5
    verdict_explainer = _VERDICT_ELI5.get(verdict, "")

    # Dataset overview mini-stats
    sample_count = report.get("sample_count", 0)
    readable_count = report.get("readable_sample_count", 0)
    analyzed_count = report.get("analyzed_sample_count", 0)
    class_counts = dist.get("class_counts", {})
    class_count = dist.get("class_count", len(class_counts))

    # Class distribution mini-chart
    class_bars_html = ""
    if class_counts:
        max_count = max(class_counts.values()) if class_counts else 1
        for cls_name, cls_count in sorted(class_counts.items(), key=lambda x: -x[1]):
            pct = (cls_count / max_count) * 100
            class_bars_html += f"""
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                <span style="min-width: 100px; font-weight: 500; font-size: 0.9em; text-align: right;">{html.escape(str(cls_name))}</span>
                <div style="flex: 1; height: 18px; background: #e5e7eb; border-radius: 4px; overflow: hidden;">
                    <div style="width: {pct:.1f}%; height: 100%; background: linear-gradient(90deg, #3b82f6, #6366f1); border-radius: 4px;"></div>
                </div>
                <span style="min-width: 50px; font-size: 0.85em; color: #64748b;">{cls_count:,}</span>
            </div>
            """

    # Manifest HTML
    manifest_html = ""
    if manifest:
        manifest_action_eli5 = {
            "REMOVE_CORRUPT": "Delete this file — it's broken and can't be used",
            "REMOVE_DUPLICATE": "Remove this copy — keeping one version is enough",
            "RELABEL_SAMPLE": "Check and fix the label — our analysis suggests it might be wrong",
            "RECAPTURE_OR_FILTER": "Replace or remove — this image is too low quality to be useful",
        }
        manifest_rows = ""
        for m in manifest[:15]:
            action_text = manifest_action_eli5.get(m.get("action", ""), m.get("action", ""))
            manifest_rows += f"""<tr>
                <td><code>{html.escape(m['sample_ref'])}</code></td>
                <td>
                    <span class='tag'>{html.escape(m['action'])}</span>
                    <div class="eli5-hint">{html.escape(action_text)}</div>
                </td>
                <td>{html.escape(m['target_dimension'])}</td>
                <td>{html.escape(m['reason'])}</td>
                <td><code>{html.escape(str(m.get('suggested_value', '')))}</code></td>
            </tr>"""
        manifest_html = f"""
        <table>
          <thead>
            <tr>
              <th>Image File</th>
              <th>What To Do</th>
              <th>Area</th>
              <th>Why</th>
              <th>Suggested Fix</th>
            </tr>
          </thead>
          <tbody>
            {manifest_rows}
          </tbody>
        </table>
        """
        if len(manifest) > 15:
            manifest_html += f'<div class="eli5-hint" style="margin-top: 8px;">Showing the first 15 of {len(manifest)} items. Download the full list via the API.</div>'
    else:
        manifest_html = '<p style="color: #059669;">✅ No individual images need fixing. Everything looks good at the sample level!</p>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dataset Health Report - {html.escape(str(report.get('dataset_fingerprint', 'DIA 2.0'))[:12])}</title>
<style>
  :root {{
    --bg: #f8fafc;
    --card-bg: #ffffff;
    --text: #1f2937;
    --border: #e2e8f0;
    --primary: #2563eb;
    --eli5: #64748b;
    --eli5-bg: #f1f5f9;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: var(--text);
    background: var(--bg);
    margin: 0;
    padding: 24px;
  }}
  .container {{
    max-width: 1100px;
    margin: 0 auto;
  }}
  .header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 2px solid var(--border);
    padding-bottom: 16px;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 12px;
  }}
  .card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }}
  .section-title {{
    margin-top: 0;
    font-size: 1.4em;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .section-subtitle {{
    font-size: 0.92em;
    color: var(--eli5);
    margin-top: -6px;
    margin-bottom: 16px;
    line-height: 1.5;
  }}
  .exec-summary {{
    display: flex;
    gap: 24px;
    align-items: center;
    flex-wrap: wrap;
  }}
  .score-box {{
    background: {badge_bg};
    border: 2px solid {badge_border};
    border-radius: 16px;
    padding: 28px;
    text-align: center;
    min-width: 180px;
  }}
  .score-number {{
    font-size: 3.5em;
    font-weight: 800;
    color: {score_color};
    line-height: 1;
  }}
  .verdict {{
    font-size: 1.1em;
    font-weight: 700;
    color: {score_color};
    margin-top: 8px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 12px;
  }}
  th, td {{
    padding: 12px 14px;
    text-align: left;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
  }}
  th {{
    background: #f1f5f9;
    font-weight: 600;
    font-size: 0.9em;
  }}
  .tag {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.8em;
    font-weight: 600;
    background: #f1f5f9;
    color: #475569;
  }}
  .tag-critical {{ background: #fef2f2; color: #b91c1c; }}
  .tag-high {{ background: #fef3c7; color: #92400e; }}
  .tag-medium {{ background: #eff6ff; color: #1e40af; }}
  .tag-low {{ background: #f0fdf4; color: #166534; }}
  .tag-info {{ background: #f1f5f9; color: #475569; }}
  .tag-warning {{ background: #fef3c7; color: #92400e; }}
  .badge-do-first {{
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: #fff;
    padding: 4px 12px;
    border-radius: 6px;
    font-size: 0.8em;
    font-weight: 700;
  }}
  .eli5-hint {{
    font-size: 0.82em;
    color: var(--eli5);
    margin-top: 3px;
    font-style: italic;
    line-height: 1.4;
  }}
  .eli5-box {{
    background: var(--eli5-bg);
    border: 1px solid var(--border);
    border-left: 3px solid #3b82f6;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 0.9em;
    margin-top: 8px;
    color: #334155;
    line-height: 1.5;
  }}
  .what-we-found {{
    background: #fef2f2;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 10px;
    font-size: 0.95em;
  }}
  .what-we-found-label {{
    font-weight: 700;
    font-size: 0.85em;
    color: #b91c1c;
    margin-bottom: 4px;
  }}
  .what-to-do {{
    background: #f0fdf4;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 6px;
    font-size: 0.95em;
  }}
  .what-to-do-label {{
    font-weight: 700;
    font-size: 0.85em;
    color: #166534;
    margin-bottom: 4px;
  }}
  .why-label {{
    font-weight: 700;
    font-size: 0.85em;
    color: #1e40af;
    margin-bottom: 4px;
  }}
  .trade-off-box {{
    margin-top: 8px;
    padding: 8px 12px;
    background: #fffbeb;
    border: 1px solid #fbbf24;
    border-radius: 6px;
    font-size: 0.88em;
    color: #92400e;
  }}
  .confound-card {{
    border-left: 4px solid #ef4444;
  }}
  .recommendation-card {{
    border-left: 4px solid #3b82f6;
  }}
  .stat-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 16px;
    margin: 16px 0;
  }}
  .stat-card {{
    background: var(--eli5-bg);
    border-radius: 10px;
    padding: 16px;
    text-align: center;
  }}
  .stat-number {{
    font-size: 1.8em;
    font-weight: 700;
    color: var(--primary);
    line-height: 1.2;
  }}
  .stat-label {{
    font-size: 0.85em;
    color: var(--eli5);
    margin-top: 4px;
  }}
  .formula-box {{
    font-size: 0.85em;
    background: var(--eli5-bg);
    padding: 12px;
    border-radius: 8px;
    border: 1px solid var(--border);
    margin-top: 10px;
  }}
  @media print {{
    body {{ background: #fff; padding: 0; }}
    .card {{ box-shadow: none; border: 1px solid #ccc; page-break-inside: avoid; }}
  }}
  @media (max-width: 700px) {{
    .exec-summary {{ flex-direction: column; }}
    .stat-grid {{ grid-template-columns: 1fr 1fr; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <h1 style="margin: 0; font-size: 1.8em;">📊 Dataset Health Report</h1>
      <div style="font-size: 0.88em; color: #64748b;">Dataset Integrity Analyzer 2.0</div>
      <div class="eli5-hint">This report checks your image dataset across 6 key areas to tell you if it's ready for AI training.</div>
    </div>
    <div style="text-align: right; font-size: 0.85em; color: #64748b;">
      <div><strong>Date:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</div>
      <div><strong>ID:</strong> {html.escape(str(report.get('dataset_fingerprint', 'N/A'))[:16])}...</div>
      <div class="eli5-hint">A unique fingerprint so you can track which version of your dataset this report is for</div>
    </div>
  </div>

  <!-- 1. Executive Summary (REQ-89.1) -->
  <div class="card">
    <h2 class="section-title">📋 The Bottom Line</h2>
    <div class="section-subtitle">
      A single score that summarises how ready your dataset is for training an AI model. Higher is better.
    </div>
    <div class="exec-summary">
      <div class="score-box">
        <div class="score-number">{f"{score:.0f}" if score is not None else "--"}</div>
        <div style="font-size: 0.85em; color: #64748b;">out of 100</div>
        <div class="verdict">{html.escape(verdict)}</div>
      </div>
      <div style="flex: 1; min-width: 280px;">
        <div class="eli5-box">
          <strong>What does this mean?</strong><br>
          {html.escape(verdict_explainer)}
        </div>
        <div class="stat-grid">
          <div class="stat-card">
            <div class="stat-number">{sample_count:,}</div>
            <div class="stat-label">Total images</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{class_count}</div>
            <div class="stat-label">Categories</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{readable_count:,}</div>
            <div class="stat-label">Readable images</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{coverage:.0f}%</div>
            <div class="stat-label">Audit coverage</div>
            <div class="eli5-hint">How much of the evaluation we could complete</div>
          </div>
        </div>
        {f'<div style="color: #b91c1c; font-size: 0.9em; margin-top: 8px; padding: 8px 12px; background: #fef2f2; border-radius: 8px;"><strong>🚨 Safety Gate Triggered:</strong> A critical check failed (e.g. data leaking between splits, or a very low dimension score). This forces the verdict to "Not Ready" regardless of the overall number.<div class="eli5-hint">Think of it like a car that scores well on comfort but fails the brakes test — it can\\'t be driven until the brakes are fixed.</div></div>' if readiness.get('hard_gate', {}).get('triggered') else ''}
      </div>
    </div>
    <details style="margin-top: 14px;">
      <summary style="cursor: pointer; font-size: 0.88em; color: var(--primary); font-weight: 600;">🔧 Technical details (click to expand)</summary>
      <div class="formula-box">
        <strong>Scoring formula:</strong> {html.escape(str(readiness.get('formula', '')))}
      </div>
    </details>
  </div>

  <!-- 1.5 Class Distribution (visual) -->
  {f'''
  <div class="card">
    <h2 class="section-title">📁 What's In Your Dataset</h2>
    <div class="section-subtitle">
      How many images are in each category. Ideally, all bars should be roughly the same length.
    </div>
    {class_bars_html}
    <div class="eli5-hint" style="margin-top: 8px;">If one bar is much longer than another, it means the AI will see far more examples of that category and might become biased towards it.</div>
  </div>
  ''' if class_bars_html else ''}

  <!-- 2. Unified Summary Table (REQ-90) -->
  <div class="card">
    <h2 class="section-title">🏥 Health Check Results by Area</h2>
    <div class="section-subtitle">
      Your dataset was evaluated across six areas. Each gets a score from 0 to 100. The "Weight" column shows how
      much each area contributes to the overall score.
    </div>
    <table>
      <thead>
        <tr>
          <th>Area</th>
          <th>Measurements</th>
          <th style="width: 220px;">Score (0–100)</th>
          <th>Weight</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {table_rows_html}
      </tbody>
    </table>
    <div class="eli5-hint" style="margin-top: 10px;">
      💡 <strong>Reading tip:</strong> A score of 100 means perfect in that area. Below 40 means there's a serious problem.
      The "Weight" tells you how important that area is to the final score — higher weight = bigger impact.
    </div>
  </div>

  <!-- 3. Cross-Dimensional Confound Findings (REQ-62, REQ-89.4) -->
  <div class="card">
    <h2 class="section-title">🔗 Hidden Interactions Between Areas</h2>
    <div class="section-subtitle">
      Sometimes problems in one area secretly affect another area. For example, all blurry images might
      belong to one category — which would confuse the AI in a way that's hard to spot.
      We check for these hidden connections here.
    </div>
    {confounds_html}
    {absent_html}
  </div>

  <!-- 4. Ranked Recommendations (REQ-83, REQ-89.7) -->
  <div class="card">
    <h2 class="section-title">🛠️ What You Should Do Next</h2>
    <div class="section-subtitle">
      A prioritised to-do list to improve your dataset. Items are ranked by impact — the ones at the top
      will give you the biggest improvement for the least effort. Items marked "Do This First" are the best
      bang for your buck.
    </div>
    {recs_html if recs_html else '<div class="eli5-box">✅ No significant issues found. Your dataset looks good across all evaluated areas!</div>'}
  </div>

  <!-- 5. Actionable Remediation Manifest (REQ-86) -->
  <div class="card">
    <h2 class="section-title">📝 Individual Image Actions</h2>
    <div class="section-subtitle">
      {len(manifest)} specific image(s) that need attention. This is the "fix list" — each row tells you
      exactly which image to fix and what to do with it.
      {' You can download the complete list as a CSV file via the API.' if manifest else ''}
    </div>
    {manifest_html}
  </div>

  <!-- 6. Methodology & Reproducibility Appendix (REQ-89.8) -->
  <div class="card">
    <h2 class="section-title">🔬 How We Calculated This</h2>
    <div class="section-subtitle">
      Technical details about the tools and methods used, so anyone can reproduce these results.
    </div>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; font-size: 0.9em;">
      <div>
        <strong>Software Versions:</strong>
        <ul>
          <li>DIA Core: 2.0.0</li>
          <li>Scoring Engine: {html.escape(str(readiness.get('version', 'readiness-v2')))}</li>
          <li>Image Analysis: {html.escape(str(report.get('model_versions', {}).get('embedding') or 'ResNet-18'))}</li>
        </ul>
        <div class="eli5-hint">These version numbers let someone re-run the exact same analysis later and get the same results.</div>
      </div>
      <div>
        <strong>How Images Were Selected:</strong>
        <ul>
          <li>Method: {html.escape(str(report.get('sampling', {}).get('strategy', 'deterministic')))}</li>
          <li>Random seed: {report.get('sampling', {}).get('seed', 42)}</li>
          <li>Percentage analyzed: {report.get('sampling', {}).get('actual_rate', 1.0):.1%}</li>
          <li>Total images: {report.get('sample_count', 0):,}</li>
        </ul>
        <div class="eli5-hint">If not all images were analyzed (sampling rate &lt; 100%), a representative sample was chosen to save time while keeping results accurate.</div>
      </div>
    </div>
    <div style="margin-top: 14px; font-size: 0.82em; color: #64748b; border-top: 1px solid var(--border); padding-top: 10px;">
      <em>⚖️ Important disclaimer:</em> {html.escape(str(report.get('disclaimer', '')))}
    </div>
  </div>
</div>
</body>
</html>
"""
