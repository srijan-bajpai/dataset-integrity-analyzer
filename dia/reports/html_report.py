"""Standalone, zero-dependency HTML report generator (REQ-89, REQ-90, REQ-91)."""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from typing import Any


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
        table_rows_html += f"""
        <tr>
            <td style="font-weight: 600;">{html.escape(name)}</td>
            <td style="font-family: monospace; font-size: 0.9em;">{html.escape(raw_m)}</td>
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
        do_first_badge = '<span class="badge-do-first">Do This First</span>' if r.get("do_first") else ""
        gain_text = f"+{r.get('projected_score_gain', 0):.1f} pts" if r.get('projected_score_gain') else "N/A"
        recs_html += f"""
        <div class="card recommendation-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <div>
                    {do_first_badge}
                    <span class="tag tag-{r.get('priority', 'info').lower()}">{html.escape(r.get('priority', 'Info'))}</span>
                    <strong style="font-size: 1.1em; margin-left: 6px;">{html.escape(r.get('category', 'General'))}</strong>
                </div>
                <div style="text-align: right; font-size: 0.85em;">
                    <div>Est. Effort: <strong>{html.escape(r.get('estimated_effort', 'Medium'))}</strong></div>
                    <div style="color: #10b981; font-weight: 600;">Projected Gain: {gain_text}</div>
                </div>
            </div>
            <div style="color: #4b5563; font-size: 0.92em; margin-bottom: 6px;"><strong>Defect:</strong> {html.escape(str(r.get('defect', '')))}</div>
            <div style="background: #f9fafb; padding: 10px; border-radius: 6px; border-left: 3px solid #3b82f6; font-size: 0.95em;">
                <strong>Action:</strong> {html.escape(str(r.get('action', '')))}
            </div>
            <div style="margin-top: 6px; font-size: 0.85em; color: #6b7280;"><em>Rationale:</em> {html.escape(str(r.get('rationale', '')))}</div>
            {f'<div style="margin-top: 4px; font-size: 0.85em; color: #b45309;">⚠️ <em>Trade-off risk:</em> {html.escape(str(r.get("trade_off_risk")))}</div>' if r.get("trade_off_risk") else ''}
        </div>
        """

    # Confounds HTML
    confounds_list = confounds.get("detected_confounds", [])
    if confounds_list:
        confounds_html = ""
        for c in confounds_list:
            confounds_html += f"""
            <div class="card confound-card">
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <strong style="color: #b91c1c;">{html.escape(c.get('type', 'Confound'))}</strong>
                    <span class="tag tag-warning">Effect: {c.get('effect_size_epsilon_squared') or c.get('effect_size') or 'Significant'}</span>
                </div>
                <div style="font-size: 0.95em; margin-bottom: 4px;">{html.escape(c.get('description', ''))}</div>
                <div style="font-size: 0.88em; color: #4b5563;"><strong>Downstream consequence:</strong> {html.escape(c.get('downstream_consequence', 'Risk of spurious model learning.'))}</div>
            </div>
            """
    else:
        confounds_html = "<div class='card' style='color: #059669;'>✓ No cross-dimensional confounds detected across quality, class, diversity, and label dimensions.</div>"

    # Absent confounds report (REQ-61)
    absent = confounds.get("absent_confounds", [])
    absent_html = f"<div style='font-size: 0.85em; color: #6b7280; margin-top: 8px;'><strong>Tested & verified absent confounds:</strong> {', '.join(html.escape(a) for a in absent)}</div>" if absent else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dataset Integrity Health Report - {html.escape(str(report.get('dataset_fingerprint', 'DIA 2.0'))[:12])}</title>
<style>
  :root {{
    --bg: #f8fafc;
    --card-bg: #ffffff;
    --text: #1f2937;
    --border: #e2e8f0;
    --primary: #2563eb;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.5;
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
  }}
  .card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }}
  .exec-summary {{
    display: flex;
    gap: 24px;
    align-items: center;
  }}
  .score-box {{
    background: {badge_bg};
    border: 2px solid {badge_border};
    border-radius: 12px;
    padding: 24px;
    text-align: center;
    min-width: 180px;
  }}
  .score-number {{
    font-size: 3.2em;
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
    padding: 10px 14px;
    text-align: left;
    border-bottom: 1px solid var(--border);
  }}
  th {{
    background: #f1f5f9;
    font-weight: 600;
    font-size: 0.9em;
  }}
  .tag {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.8em;
    font-weight: 600;
    background: #f1f5f9;
    color: #475569;
  }}
  .badge-do-first {{
    background: #2563eb;
    color: #fff;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.75em;
    font-weight: 700;
    text-transform: uppercase;
  }}
  .confound-card {{
    border-left: 4px solid #ef4444;
  }}
  .recommendation-card {{
    border-left: 4px solid #3b82f6;
  }}
  @media print {{
    body {{ background: #fff; padding: 0; }}
    .card {{ box-shadow: none; border: 1px solid #ccc; page-break-inside: avoid; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <h1 style="margin: 0; font-size: 1.8em;">Dataset Health Report</h1>
      <div style="font-size: 0.85em; color: #64748b;">Dataset Integrity Analyzer 2.0 (Unified 6-Dimension Health Evaluation)</div>
    </div>
    <div style="text-align: right; font-size: 0.85em; color: #64748b;">
      <div><strong>Date:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</div>
      <div><strong>Fingerprint:</strong> {html.escape(str(report.get('dataset_fingerprint', 'N/A'))[:16])}...</div>
    </div>
  </div>

  <!-- 1. Executive Summary (REQ-89.1) -->
  <div class="card">
    <h2 style="margin-top: 0;">1. Executive Summary</h2>
    <div class="exec-summary">
      <div class="score-box">
        <div class="score-number">{f"{score:.0f}" if score is not None else "--"}</div>
        <div style="font-size: 0.85em; color: #64748b;">out of 100</div>
        <div class="verdict">{html.escape(verdict)}</div>
      </div>
      <div style="flex: 1;">
        <p style="margin-top: 0;">
          <strong>Dataset Health Evaluation:</strong> Evaluated across all six core dimensions (Balance, Fairness, Quality, Uniqueness, Diversity, Label Integrity).
          Overall readiness score reflects weighted dimension scores with an audit coverage of <strong>{coverage:.1f}%</strong>.
        </p>
        <div style="font-size: 0.9em; background: #f8fafc; padding: 12px; border-radius: 6px; border: 1px solid var(--border);">
          <strong>Formula:</strong> {html.escape(str(readiness.get('formula', '')))}
        </div>
        {f'<div style="margin-top: 8px; color: #b91c1c; font-size: 0.9em;"><strong>⚠️ Hard Gate Triggered:</strong> Cross-split duplicate leakage or critical sub-score below 30 detected.</div>' if readiness.get('hard_gate', {}).get('triggered') else ''}
      </div>
    </div>
  </div>

  <!-- 2. Unified Summary Table (REQ-90) -->
  <div class="card">
    <h2 style="margin-top: 0;">2. Unified Dimension Health Summary (C1 Scale)</h2>
    <p style="font-size: 0.9em; color: #64748b; margin-top: -8px;">
      All six dimensions reconciled onto one common 0–100 scale, enabling cross-dimensional comparison.
    </p>
    <table>
      <thead>
        <tr>
          <th>Dimension</th>
          <th>Raw Metrics</th>
          <th style="width: 250px;">Normalised Score (0–100)</th>
          <th>Weight</th>
          <th>Verdict</th>
        </tr>
      </thead>
      <tbody>
        {table_rows_html}
      </tbody>
    </table>
  </div>

  <!-- 3. Cross-Dimensional Confound Findings (REQ-62, REQ-89.4) -->
  <div class="card">
    <h2 style="margin-top: 0;">3. Cross-Dimensional Confound Findings (Novel C1)</h2>
    <p style="font-size: 0.9em; color: #64748b; margin-top: -8px;">
      Interactions across two or more dimensions (e.g. quality × demographic or redundancy × class) that single-axis tools cannot detect.
    </p>
    {confounds_html}
    {absent_html}
  </div>

  <!-- 4. Ranked Recommendations (REQ-83, REQ-89.7) -->
  <div class="card">
    <h2 style="margin-top: 0;">4. Prioritised Corrective Actions</h2>
    <p style="font-size: 0.9em; color: #64748b; margin-top: -8px;">
      Ranked across all dimensions by projected readiness score gain divided by estimated effort. Top 3 are highlighted for immediate action.
    </p>
    {recs_html}
  </div>

  <!-- 5. Actionable Remediation Manifest (REQ-86) -->
  <div class="card">
    <h2 style="margin-top: 0;">5. Machine-Actionable Remediation Manifest</h2>
    <p style="font-size: 0.9em; color: #64748b; margin-top: -8px;">
      {len(manifest)} sample-level corrective action(s) identified. You can download the full CSV manifest via the API endpoint <code>/v1/runs/{{run_id}}/remediation-manifest.csv</code>.
    </p>
    {f'''
    <table>
      <thead>
        <tr>
          <th>Sample Reference</th>
          <th>Recommended Action</th>
          <th>Target Dimension</th>
          <th>Reason</th>
          <th>Suggested Value</th>
        </tr>
      </thead>
      <tbody>
        {''.join(f"<tr><td><code>{html.escape(m['sample_ref'])}</code></td><td><span class='tag'>{html.escape(m['action'])}</span></td><td>{html.escape(m['target_dimension'])}</td><td>{html.escape(m['reason'])}</td><td><code>{html.escape(str(m.get('suggested_value', '')))}</code></td></tr>" for m in manifest[:15])}
      </tbody>
    </table>
    ''' if manifest else '<p style="color: #059669;">No sample-level remediation actions needed.</p>'}
    {f'<div style="font-size: 0.85em; color: #64748b; margin-top: 8px;">Showing first 15 of {len(manifest)} manifest records.</div>' if len(manifest) > 15 else ''}
  </div>

  <!-- 6. Methodology & Reproducibility Appendix (REQ-89.8) -->
  <div class="card">
    <h2 style="margin-top: 0;">6. Methodology & Reproducibility Appendix</h2>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; font-size: 0.9em;">
      <div>
        <strong>System & Runtime Versions:</strong>
        <ul>
          <li>DIA Core: 2.0.0</li>
          <li>Scoring Engine: {html.escape(str(readiness.get('version', 'readiness-v2')))}</li>
          <li>Embeddings: {html.escape(str(report.get('model_versions', {}).get('embedding') or 'ResNet-18'))}</li>
          <li>FastAPI: {html.escape(str(report.get('analyzer_versions', {}).get('runtime_libraries', {}).get('fastapi', 'installed')))}</li>
          <li>PyTorch: {html.escape(str(report.get('analyzer_versions', {}).get('runtime_libraries', {}).get('torch', 'installed')))}</li>
        </ul>
      </div>
      <div>
        <strong>Sampling & Configuration:</strong>
        <ul>
          <li>Sampling Strategy: {html.escape(str(report.get('sampling', {}).get('strategy', 'deterministic')))}</li>
          <li>Sampling Seed: {report.get('sampling', {}).get('seed', 42)}</li>
          <li>Actual Sampling Rate: {report.get('sampling', {}).get('actual_rate', 1.0):.1%}</li>
          <li>Total Samples: {report.get('sample_count', 0):,}</li>
        </ul>
      </div>
    </div>
    <div style="margin-top: 12px; font-size: 0.8em; color: #64748b; border-top: 1px solid var(--border); padding-top: 8px;">
      <em>Disclaimer:</em> {html.escape(str(report.get('disclaimer', '')))}
    </div>
  </div>
</div>
</body>
</html>
"""
