"""Exact and perceptual near-duplicate detection."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import imagehash
import numpy as np
import pandas as pd
from PIL import Image

from .base import BaseAnalyzer


class DuplicatesAnalyzer(BaseAnalyzer):
    def __init__(self, df: pd.DataFrame, near_distance: int = 4, embeddings: np.ndarray | None = None,
                 embedding_cosine_threshold: float = 0.98):
        super().__init__(df)
        self.near_distance = near_distance
        self.embeddings = None if embeddings is None else np.asarray(embeddings, dtype=np.float32)
        self.embedding_cosine_threshold = embedding_cosine_threshold

    def run(self) -> dict[str, Any]:
        hashes: list[str | None] = []
        exact_hashes: list[str | None] = []
        for path in self.df["path"]:
            try:
                with Image.open(path) as image:
                    hashes.append(str(imagehash.phash(image.convert("RGB"))))
                if "content_sha256" in self.df.columns and pd.notna(self.df.loc[self.df["path"] == path, "content_sha256"].iloc[0]):
                    exact_hashes.append(str(self.df.loc[self.df["path"] == path, "content_sha256"].iloc[0]))
                else:
                    import hashlib
                    digest = hashlib.sha256()
                    with open(path, "rb") as f:
                        for block in iter(lambda: f.read(1024 * 1024), b""):
                            digest.update(block)
                    exact_hashes.append(digest.hexdigest())
            except (OSError, ValueError, IndexError):
                hashes.append(None)
                exact_hashes.append(None)

        n = len(self.df)
        self.df["phash"] = hashes
        exact_map: dict[str, list[int]] = defaultdict(list)
        for i, value in enumerate(exact_hashes):
            if value:
                exact_map[value].append(i)
        exact_groups = [indices for indices in exact_map.values() if len(indices) > 1]
        exact_duplicate_count = sum(len(group) - 1 for group in exact_groups)
        exact_pairs = {frozenset((a, b)) for group in exact_groups for pos, a in enumerate(group) for b in group[pos + 1:]}
        if self.embeddings is not None and len(self.embeddings) != n:
            raise ValueError("Embedding count does not match duplicate candidates.")
        normalized_embeddings = None
        if self.embeddings is not None:
            norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
            normalized_embeddings = self.embeddings / np.maximum(norms, 1e-12)

        valid = [(i, imagehash.hex_to_hash(value)) for i, value in enumerate(hashes) if value]
        parent = list(range(n))

        def find(i: int) -> int:
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        # BK-tree search returns only hashes within the Hamming threshold, avoiding
        # an all-pairs scan. Keep indices per unique hash to handle repeated hashes.
        def distance(a: int, b: int) -> int:
            return (a ^ b).bit_count()
        def insert_node(node: dict[str, Any], value: int, sample_index: int) -> None:
            d = distance(value, node["value"])
            if d == 0:
                node["indices"].append(sample_index)
            elif d in node["children"]:
                insert_node(node["children"][d], value, sample_index)
            else:
                node["children"][d] = {"value": value, "indices": [sample_index], "children": {}}
        root: dict[str, Any] | None = None
        for i, hashed in valid:
            value = int(str(hashed), 16)
            if root is None:
                root = {"value": value, "indices": [i], "children": {}}
                continue
            stack = [root]
            while stack:
                node = stack.pop()
                d = distance(value, node["value"])
                if d <= self.near_distance:
                    for j in node["indices"]:
                        exact_match = frozenset((i, j)) in exact_pairs
                        embedding_match = (
                            normalized_embeddings is not None
                            and float(np.dot(normalized_embeddings[i], normalized_embeddings[j])) >= self.embedding_cosine_threshold
                        )
                        if exact_match or normalized_embeddings is None or embedding_match:
                            union(i, j)
                low, high = d - self.near_distance, d + self.near_distance
                stack.extend(child for edge, child in node["children"].items() if low <= edge <= high)
            insert_node(root, value, i)
        groups: dict[int, list[int]] = defaultdict(list)
        for i, _ in valid:
            groups[find(i)].append(i)
        near_groups = [group for group in groups.values() if len(group) > 1]
        ids: list[int | None] = [None] * n
        for gid, group in enumerate(near_groups):
            for i in group:
                ids[i] = gid
        self.df["duplicate_group"] = ids

        cross_split_groups = 0
        conflicting_label_groups = 0
        if "split" in self.df.columns:
            for group in near_groups:
                if self.df.iloc[group]["split"].nunique(dropna=True) > 1:
                    cross_split_groups += 1
        if "ground_truth_class" in self.df.columns:
            conflicting_label_groups = sum(
                self.df.iloc[group]["ground_truth_class"].dropna().astype(str).nunique() > 1
                for group in near_groups
            )
        redundant = sum(len(group) - 1 for group in near_groups)
        self.df["flag_duplicate"] = [gid is not None for gid in ids]
        return {
            "exact_duplicate_count": exact_duplicate_count,
            "exact_duplicate_groups": len(exact_groups),
            "near_duplicate_count": redundant,
            "near_duplicate_groups": len(near_groups),
            "cross_split_duplicate_groups": cross_split_groups,
            "conflicting_label_duplicate_groups": int(conflicting_label_groups),
            "redundancy_ratio": redundant / n if n else 0.0,
            "near_duplicate_hamming_threshold": self.near_distance,
            "embedding_confirmation": "cosine_similarity" if normalized_embeddings is not None else "unavailable",
            "embedding_cosine_threshold": self.embedding_cosine_threshold if normalized_embeddings is not None else None,
        }
