"""Plain, evidence-linked remediation suggestions."""

from typing import Any


class RecommendationEngine:
    def __init__(self, agg_results: dict[str, Any]):
        self.agg = agg_results

    def generate(self) -> list[dict[str, str]]:
        recs: list[dict[str, str]] = []
        fairness = self.agg.get("fairness", {})
        for finding in fairness.get("findings", []):
            recs.append({
                "priority": "High" if finding.get("severity") == "warning" else "Review",
                "category": "Group representation",
                "evidence": finding.get("code", "GROUP_REPRESENTATION_GAP"),
                "action": "Review collection and sampling for this group against the target you supplied. Confirm that the target reflects the intended use before changing the dataset.",
            })

        distribution = self.agg.get("distribution", {})
        ratio = distribution.get("imbalance_ratio")
        if ratio is not None and ratio > 3:
            recs.append({
                "priority": "High" if ratio > 10 else "Medium", "category": "Class balance",
                "evidence": f"Majority-to-minority ratio is {ratio:.2f}:1.",
                "action": "Review whether the class counts match the intended task. Consider collecting minority examples or using a documented sampling strategy.",
            })

        quality = self.agg.get("quality", {})
        defects = quality.get("defect_rate_pct")
        if defects is not None and defects >= 5:
            recs.append({
                "priority": "Medium", "category": "Image quality",
                "evidence": f"{defects:.1f}% of readable images failed at least one quality check.",
                "action": "Review flagged images and compare quality across classes and groups before removing or altering samples.",
            })

        duplicates = self.agg.get("duplicates", {})
        if duplicates.get("near_duplicate_count", 0):
            recs.append({
                "priority": "High" if duplicates.get("cross_split_duplicate_groups", 0) else "Medium",
                "category": "Duplicates",
                "evidence": f"{duplicates['near_duplicate_count']} redundant image(s); {duplicates.get('cross_split_duplicate_groups', 0)} group(s) cross splits.",
                "action": "Review duplicate groups and keep related images in the same data split to reduce evaluation leakage.",
            })

        for finding in self.agg.get("metadata", {}).get("findings", []):
            if finding.get("code") == "METADATA_MISSING_VALUES":
                recs.append({
                    "priority": "Medium", "category": "Metadata quality",
                    "evidence": finding.get("description", "Missing attribute values were found."),
                    "action": "Check the source manifest and correct missing values where reliable labels are available. Keep unknown values explicitly unknown.",
                })

        for finding in self.agg.get("confounds", {}).get("detected_confounds", []):
            recs.append({
                "priority": "Review", "category": "Cross-dimension finding",
                "evidence": finding.get("description", finding.get("type", "A group difference was found.")),
                "action": "Inspect the affected samples and group summaries. Treat this result as a signal to investigate, not proof of causation.",
            })

        if not recs:
            recs.append({
                "priority": "Info", "category": "Review",
                "evidence": "No configured finding thresholds were crossed.",
                "action": "Review sample counts and dimensions marked unavailable before deciding the dataset is ready.",
            })
        return recs
