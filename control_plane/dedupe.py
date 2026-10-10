"""Persistent cut ledger that prevents replaying previously-used source ranges."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path


@dataclass(frozen=True)
class Cut:
    source_id: str
    start_ms: int
    end_ms: int
    media_sha256: str

    def validate(self) -> None:
        if not self.source_id:
            raise ValueError("source_id_required")
        if self.start_ms < 0 or self.end_ms <= self.start_ms:
            raise ValueError("invalid_interval")
        if len(self.media_sha256) != 64:
            raise ValueError("invalid_sha256")


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def overlap_ratio(a_start: int, a_end: int, b_start: int, b_end: int) -> float:
    overlap = max(0, min(a_end, b_end) - max(a_start, b_start))
    if overlap == 0:
        return 0.0
    shorter = min(a_end - a_start, b_end - b_start)
    return overlap / shorter


class CutLedger:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.rows: list[Cut] = []
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.rows = [Cut(**row) for row in data]
            for row in self.rows:
                row.validate()

    def seen_hash(self, media_sha256: str) -> bool:
        return any(row.media_sha256 == media_sha256 for row in self.rows)

    def overlaps(self, source_id: str, start_ms: int, end_ms: int, *, threshold: float = 0.0) -> bool:
        """Reject any repeated source interval by default; threshold may relax this explicitly."""
        if not 0 <= threshold <= 1:
            raise ValueError("threshold_out_of_range")
        for row in self.rows:
            if row.source_id != source_id:
                continue
            ratio = overlap_ratio(start_ms, end_ms, row.start_ms, row.end_ms)
            if (threshold == 0 and ratio > 0) or (threshold > 0 and ratio >= threshold):
                return True
        return False

    def eligible(self, cut: Cut, *, overlap_threshold: float = 0.0) -> bool:
        cut.validate()
        return not self.seen_hash(cut.media_sha256) and not self.overlaps(
            cut.source_id, cut.start_ms, cut.end_ms, threshold=overlap_threshold
        )

    def reserve(self, cut: Cut, *, overlap_threshold: float = 0.0) -> None:
        if not self.eligible(cut, overlap_threshold=overlap_threshold):
            raise RuntimeError("duplicate_cut")
        self.rows.append(cut)
        self._save()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(
            json.dumps([asdict(row) for row in self.rows], ensure_ascii=False, sort_keys=True, indent=2),
            encoding="utf-8",
        )
        tmp.replace(self.path)
