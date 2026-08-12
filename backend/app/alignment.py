"""Embedding-based monotonic alignment between two paragraph sequences.

Positional alignment ("paragraph N of the original is paragraph N of the
translation") breaks the moment a paragraph is added, dropped, or split or
merged during translation - every pair after that point silently lines up
with the wrong paragraph. This scores every candidate pairing by embedding
cosine similarity instead and finds the highest-scoring monotonic path
through the two sequences with dynamic programming - the same family of
algorithm bilingual-corpus aligners such as Vecalign use - so one missing or
extra paragraph costs one gap penalty instead of desynchronising the rest of
the document.
"""

import math

DEFAULT_GAP_PENALTY = 0.15
DEFAULT_MERGE_PENALTY = 0.03

_Move = tuple[str, int, int]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _mean_pool(vectors: list[list[float]]) -> list[float]:
    dims = len(vectors[0])
    return [sum(v[d] for v in vectors) / len(vectors) for d in range(dims)]


def align_paragraphs(
    source_paragraphs: list[str],
    source_embeddings: list[list[float]],
    target_paragraphs: list[str],
    target_embeddings: list[list[float]],
    gap_penalty: float = DEFAULT_GAP_PENALTY,
    merge_penalty: float = DEFAULT_MERGE_PENALTY,
) -> list[dict]:
    """Best monotonic alignment of two paragraph sequences.

    Each output pair is a 1:1 match, a 1:2/2:1 merge (a paragraph split or
    joined during translation), or a gap - a paragraph with no counterpart
    on the other side, returned with the other side's text empty so the
    caller (a review UI, in practice) can see and fix it rather than have it
    silently paired with the wrong neighbour.

    Merged-span embeddings are approximated by mean-pooling the individual
    paragraph embeddings rather than re-embedding the concatenated text,
    which would need embedding every possible span combination. This is the
    same trade-off production aligners make for the same reason.
    """
    n, m = len(source_paragraphs), len(target_paragraphs)
    if n == 0 and m == 0:
        return []

    def span_similarity(i_start: int, i_len: int, j_start: int, j_len: int) -> float:
        s_vec = source_embeddings[i_start] if i_len == 1 else _mean_pool(source_embeddings[i_start : i_start + i_len])
        t_vec = target_embeddings[j_start] if j_len == 1 else _mean_pool(target_embeddings[j_start : j_start + j_len])
        return _cosine(s_vec, t_vec)

    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    back: list[list[_Move | None]] = [[None] * (m + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] - gap_penalty
        back[i][0] = ("del", 1, 0)
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] - gap_penalty
        back[0][j] = ("ins", 0, 1)

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            candidates: list[tuple[float, _Move]] = [
                (dp[i - 1][j - 1] + span_similarity(i - 1, 1, j - 1, 1), ("match", 1, 1)),
                (dp[i - 1][j] - gap_penalty, ("del", 1, 0)),
                (dp[i][j - 1] - gap_penalty, ("ins", 0, 1)),
            ]
            if i >= 2:
                candidates.append(
                    (dp[i - 2][j - 1] + span_similarity(i - 2, 2, j - 1, 1) - merge_penalty, ("match", 2, 1))
                )
            if j >= 2:
                candidates.append(
                    (dp[i - 1][j - 2] + span_similarity(i - 1, 1, j - 2, 2) - merge_penalty, ("match", 1, 2))
                )
            dp[i][j], back[i][j] = max(candidates, key=lambda c: c[0])

    pairs: list[dict] = []
    i, j = n, m
    while i > 0 or j > 0:
        move, di, dj = back[i][j]
        if move == "match":
            pairs.append(
                {
                    "source_text": " ".join(source_paragraphs[i - di : i]),
                    "target_text": " ".join(target_paragraphs[j - dj : j]),
                }
            )
        elif move == "del":
            pairs.append({"source_text": source_paragraphs[i - 1], "target_text": ""})
        else:
            pairs.append({"source_text": "", "target_text": target_paragraphs[j - 1]})
        i, j = i - di, j - dj
    pairs.reverse()
    return pairs


def _positional_pairs(source_items: list[str], target_items: list[str]) -> list[dict]:
    pairs = []
    for i in range(max(len(source_items), len(target_items))):
        source_item = source_items[i] if i < len(source_items) else ""
        target_item = target_items[i] if i < len(target_items) else ""
        if source_item.strip() or target_item.strip():
            pairs.append({"source_text": source_item, "target_text": target_item})
    return pairs


def align_tables(source_tables: list[list[list[str]]], target_tables: list[list[list[str]]]) -> list[dict]:
    """Match table cells by position (table i, row j, cell k on both sides)
    instead of by embedding similarity.

    A bare cell value - an element symbol, a lone number - carries almost no
    distinguishing semantic signal for similarity search to work with, so
    align_paragraphs' approach is the wrong tool here. A table's row/column
    structure, on the other hand, is reliably preserved between an original
    and its translation: translators don't reorder or drop rows of a data
    table the way a paragraph of prose might get split, merged, or dropped.
    A table, row, or cell that has no counterpart (a genuine count/shape
    mismatch) still comes back with the other side left empty, the same
    "flag it for review" convention align_paragraphs uses for gaps.
    """
    pairs: list[dict] = []
    for t in range(max(len(source_tables), len(target_tables))):
        source_table = source_tables[t] if t < len(source_tables) else []
        target_table = target_tables[t] if t < len(target_tables) else []
        for r in range(max(len(source_table), len(target_table))):
            source_row = source_table[r] if r < len(source_table) else []
            target_row = target_table[r] if r < len(target_table) else []
            pairs.extend(_positional_pairs(source_row, target_row))
    return pairs
