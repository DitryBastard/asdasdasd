"""LLM-based alignment of a source document with its translation.

Rule-based paragraph segmentation (blank lines, physical lines) cannot
reliably tell flowing prose, a list of short reference entries, and a
heading apart - real technical documents mix all three, and no single
heuristic handled them consistently (see git history of app/alignment.py
for the two heuristics tried and abandoned here). The model itself is far
better suited to this: it reads a whole document and segments *and* aligns
it in one step, the way a person would, rather than pre-splitting into
paragraphs first and hoping the split lines up with what actually
corresponds between languages.

Table cells are handled separately (app/alignment.align_tables) and are not
part of this module's input.
"""

import json
import re

from .config import settings
from .ollama_client import OllamaClient
from .segmentation import split_paragraphs, split_sentences

ollama = OllamaClient()

ALIGNMENT_SYSTEM_PROMPT = (
    "You are an expert at aligning a document with its translation. You will be "
    "given the full text of a source document section and its translation. Break "
    "both into corresponding logical segments - a paragraph, a list item, a "
    "heading, a reference entry, whatever the natural unit is - and pair each "
    "segment with its counterpart on the other side, in the order they appear. "
    "Some segments may have no counterpart (content added, removed, or reordered "
    "between the two) - include those too, with the other side left as an empty "
    'string "". Return ONLY a JSON array of objects with exactly two string keys, '
    '"source" and "target" - no explanation, no markdown code fences, nothing '
    "before or after the array."
)

_JSON_ARRAY = re.compile(r"\[.*\]", re.DOTALL)


def _chunk_text(text: str, lang: str, max_chars: int) -> list[str]:
    """Split text into chunks no larger than max_chars, breaking at
    paragraph boundaries where possible (falling back to sentence
    boundaries for a single paragraph that alone exceeds the budget) so a
    chunk boundary is very unlikely to land mid-sentence.
    """
    text = text.strip()
    if not text:
        return []

    units: list[str] = []
    for paragraph in split_paragraphs(text):
        if len(paragraph) <= max_chars:
            units.append(paragraph)
        else:
            units.extend(split_sentences(paragraph, lang) or [paragraph])

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for unit in units:
        if current and current_len + len(unit) + 2 > max_chars:
            chunks.append("\n\n".join(current))
            current = []
            current_len = 0
        current.append(unit)
        current_len += len(unit) + 2
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def _build_alignment_prompt(source_chunk: str, target_chunk: str) -> str:
    return (
        "=== SOURCE ===\n"
        f"{source_chunk}\n\n"
        "=== TRANSLATION ===\n"
        f"{target_chunk}\n\n"
        "Output the JSON array now."
    )


def _parse_alignment_response(content: str) -> list[dict] | None:
    candidates = [content]
    match = _JSON_ARRAY.search(content)
    if match:
        candidates.append(match.group(0))

    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(data, list):
            continue
        pairs = []
        for item in data:
            if not isinstance(item, dict) or "source" not in item or "target" not in item:
                break
            pairs.append({"source_text": str(item["source"]), "target_text": str(item["target"])})
        else:
            return pairs
    return None


async def align_documents_with_llm(
    source_text: str,
    target_text: str,
    source_lang: str,
    target_lang: str,
) -> list[dict]:
    source_chunks = _chunk_text(source_text, source_lang, settings.llm_alignment_max_chars)
    target_chunks = _chunk_text(target_text, target_lang, settings.llm_alignment_max_chars)
    chunk_count = max(len(source_chunks), len(target_chunks))

    pairs: list[dict] = []
    for i in range(chunk_count):
        source_chunk = source_chunks[i] if i < len(source_chunks) else ""
        target_chunk = target_chunks[i] if i < len(target_chunks) else ""
        if not source_chunk.strip() and not target_chunk.strip():
            continue

        content = await ollama.chat(
            [
                {"role": "system", "content": ALIGNMENT_SYSTEM_PROMPT},
                {"role": "user", "content": _build_alignment_prompt(source_chunk, target_chunk)},
            ],
            temperature=0.0,
        )
        parsed = _parse_alignment_response(content)
        if parsed is None:
            # The model didn't follow the format even once for this chunk;
            # fall back to keeping the whole chunk pair as one coarse pair
            # rather than losing its content entirely.
            parsed = [{"source_text": source_chunk, "target_text": target_chunk}]
        pairs.extend(parsed)
    return pairs
