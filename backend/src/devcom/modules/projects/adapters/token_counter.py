from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TokenEstimate:
    upper_bound: int
    indicative: int
    blocking_method: str
    indicative_method: str


def estimate_tokens(text: str) -> TokenEstimate:
    """Blocking ceiling: ≤1 BPE token per UTF-8 byte (justified upper bound)."""
    upper = len(text.encode("utf-8"))
    indicative = max(1, len(text) // 4) if text else 0
    return TokenEstimate(
        upper_bound=upper,
        indicative=indicative,
        blocking_method="utf8_byte_upper_bound",
        indicative_method="char_div4_indicative",
    )


def estimate_blob_tokens(contents: tuple[str, ...]) -> TokenEstimate:
    joined = "\n".join(contents)
    return estimate_tokens(joined)
