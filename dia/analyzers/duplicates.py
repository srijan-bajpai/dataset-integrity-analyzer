"""Exact and perceptual near-duplicate detection."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import imagehash
import pandas as pd
from PIL import Image

from .base import BaseAnalyzer


class DuplicatesAnalyzer(BaseAnalyzer):
    def __init__(self, df: pd.DataFrame, near_distance: int = 4):
        super().__init__(df)
        self.near_distance = near_distance

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

        for offset, (i, h1) in enumerate(valid):
            for j, h2 in valid[offset + 1:]:
                if (h1 - h2) <= self.near_distance:
                    union(i, j)
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
        if "split" in self.df.columns:
            for group in near_groups:
                if self.df.iloc[group]["split"].nunique(dropna=True) > 1:
                    cross_split_groups += 1
        redundant = sum(len(group) - 1 for group in near_groups)
        self.df["flag_duplicate"] = [gid is not None for gid in ids]
        return {
            "exact_duplicate_count": exact_duplicate_count,
            "exact_duplicate_groups": len(exact_groups),
            "near_duplicate_count": redundant,
            "near_duplicate_groups": len(near_groups),
            "cross_split_duplicate_groups": cross_split_groups,
            "redundancy_ratio": redundant / n if n else 0.0,
            "near_duplicate_hamming_threshold": self.near_distance,
        }
