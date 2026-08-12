"""Positional alignment for table cells.

Body-paragraph alignment used to live here too (an embedding-similarity
dynamic-programming aligner), but real documents mix flowing prose, short
list-like entries, and tables - no paragraph-segmentation heuristic
consistently told those apart, so alignment quality depended entirely on
getting that segmentation right first. That approach was replaced with
app/llm_alignment.py, which hands the model raw document text and lets it
segment and align in one step.

Table cells are different: a bare cell value (an element symbol, a lone
number) carries almost no distinguishing semantic signal, so similarity
search - or a model call - is the wrong tool. A table's row/column structure
is reliably preserved between an original and its translation, so matching
by position (table i, row j, cell k on both sides) is both simpler and more
accurate here.
"""


def _positional_pairs(source_items: list[str], target_items: list[str]) -> list[dict]:
    pairs = []
    for i in range(max(len(source_items), len(target_items))):
        source_item = source_items[i] if i < len(source_items) else ""
        target_item = target_items[i] if i < len(target_items) else ""
        if source_item.strip() or target_item.strip():
            pairs.append({"source_text": source_item, "target_text": target_item})
    return pairs


def align_tables(source_tables: list[list[list[str]]], target_tables: list[list[list[str]]]) -> list[dict]:
    """Match table cells by position (table i, row j, cell k on both sides).

    A table, row, or cell that has no counterpart (a genuine count/shape
    mismatch) comes back with the other side left empty, so it is flagged
    for review rather than silently paired with the wrong neighbour.
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
