"""Command-line interface for headless/batch dataset auditing (REQ-UI-10, OR-8)."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from dia.core.ingestion import parse_dataset, safe_extract_zip
from dia.core.pipeline import run_analysis
from dia.reports.datasheet import format_datasheet_markdown
from dia.reports.html_report import render_html_report


def run_cli_analysis(
    dataset_path: str | Path,
    output_path: str | Path | None = None,
    html_path: str | Path | None = None,
    datasheet_path: str | Path | None = None,
    manifest_path: str | Path | None = None,
    sampling_rate: float = 1.0,
    predict_impact: bool = False,
    estimate_attributes: bool = False,
) -> dict[str, Any]:
    """Execute full dataset integrity audit from CLI and write requested report formats."""
    dpath = Path(dataset_path).resolve()
    if not dpath.exists():
        raise FileNotFoundError(f"Dataset path does not exist: {dpath}")

    temp_dir = None
    if dpath.is_file() and dpath.suffix.lower() == ".zip":
        temp_dir = Path(tempfile.mkdtemp(prefix="dia_cli_"))
        safe_extract_zip(dpath, temp_dir)
        extract_root = temp_dir
    else:
        extract_root = dpath

    try:
        layout, records, warnings = parse_dataset(extract_root)
        print(f"Ingested {len(records)} samples (layout: {layout}).")

        report = run_analysis(
            records,
            sampling_rate=sampling_rate,
            predict_impact=predict_impact,
            estimate_attributes=estimate_attributes,
            warnings=warnings,
        )

        readiness = report.get("results", {}).get("readiness", {})
        print(f"Audit Complete! Readiness Score: {readiness.get('overall_score')} / 100 ({readiness.get('verdict')})")

        # Save JSON report
        if output_path:
            out_p = Path(output_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(json.dumps(report, indent=2), encoding="utf-8")
            print(f"Saved JSON report to: {out_p}")

        # Save HTML report
        if html_path:
            html_p = Path(html_path)
            html_p.parent.mkdir(parents=True, exist_ok=True)
            html_p.write_text(render_html_report(report), encoding="utf-8")
            print(f"Saved HTML report to: {html_p}")

        # Save Datasheet Markdown
        if datasheet_path:
            ds_p = Path(datasheet_path)
            ds_p.parent.mkdir(parents=True, exist_ok=True)
            ds_p.write_text(format_datasheet_markdown(report), encoding="utf-8")
            print(f"Saved Datasheet Markdown to: {ds_p}")

        # Save Remediation Manifest CSV
        if manifest_path:
            man_p = Path(manifest_path)
            man_p.parent.mkdir(parents=True, exist_ok=True)
            import csv
            import io
            fieldnames = ["sample_ref", "action", "target_dimension", "reason", "current_label", "suggested_value"]
            with open(man_p, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                for row in report.get("remediation_manifest", []):
                    writer.writerow(row)
            print(f"Saved Remediation Manifest to: {man_p}")

        return report

    finally:
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="dia",
        description="Dataset Integrity Analyzer (DIA) 2.0 CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # analyze command (REQ-UI-10)
    analyze_parser = subparsers.add_parser("analyze", help="Run full integrity audit on a dataset directory or ZIP.")
    analyze_parser.add_argument("--path", required=True, help="Path to dataset directory or ZIP archive.")
    analyze_parser.add_argument("--out", help="Path to output JSON report file.")
    analyze_parser.add_argument("--html", help="Path to output standalone HTML report.")
    analyze_parser.add_argument("--datasheet", help="Path to output Markdown Datasheet / Model Card.")
    analyze_parser.add_argument("--manifest", help="Path to output Remediation Manifest CSV.")
    analyze_parser.add_argument("--sample-rate", type=float, default=1.0, help="Sampling rate (0, 1].")
    analyze_parser.add_argument("--predict-impact", action="store_true", help="Enable validated bias impact prediction.")
    analyze_parser.add_argument("--estimate-attributes", action="store_true", help="Enable opt-in attribute suggestions.")

    args = parser.parse_args()

    if args.command == "analyze":
        try:
            run_cli_analysis(
                dataset_path=args.path,
                output_path=args.out,
                html_path=args.html,
                datasheet_path=args.datasheet,
                manifest_path=args.manifest,
                sampling_rate=args.sample_rate,
                predict_impact=args.predict_impact,
                estimate_attributes=args.estimate_attributes,
            )
        except Exception as exc:
            print(f"Error during analysis: {exc}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
