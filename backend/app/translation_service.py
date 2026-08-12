import re

from .config import settings
from .ollama_client import OllamaClient
from .segmentation import split_paragraphs, split_sentences
from .vector_store import vector_store

ollama = OllamaClient()

SYSTEM_PROMPT = (
    "You are an expert technical translator. Translate precisely and naturally, "
    "preserving technical terminology, numbers, units, formatting, and any inline "
    "code, file paths, or values in quotes exactly as they appear. When reference "
    "translations from a translation memory are provided, reuse their terminology "
    "and phrasing for consistency whenever it genuinely fits the sentence - ignore "
    "a reference if it does not apply. Return only the requested translation(s), "
    "with no explanations or extra commentary."
)

_NUMBERED_LINE = re.compile(r"^\s*(\d+)[.)]\s*(.*)$")


def _best_match(candidates: list[dict]) -> dict | None:
    """Classify the closest translation-memory hit for one sentence.

    Below the fuzzy threshold a candidate is considered noise and ignored.
    Between fuzzy and exact it is returned as a reference for the model to
    draw on. At/above the exact threshold the stored translation is reliable
    enough to reuse verbatim, without ever calling the model.
    """
    if not candidates:
        return None
    best = max(candidates, key=lambda c: c["similarity"])
    if best["similarity"] < settings.fuzzy_match_threshold:
        return None
    match_type = "exact" if best["similarity"] >= settings.exact_match_threshold else "fuzzy"
    return {
        "type": match_type,
        "similarity": best["similarity"],
        "memory_source": best["source_text"],
        "memory_target": best["target_text"],
        "document_title": best.get("document_title") or "",
    }


def _parse_numbered_response(text: str, expected: int) -> list[str] | None:
    results: dict[int, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        match = _NUMBERED_LINE.match(line)
        if match:
            results[int(match.group(1))] = match.group(2).strip()
    if len(results) != expected or any(i not in results for i in range(1, expected + 1)):
        return None
    return [results[i] for i in range(1, expected + 1)]


def _build_reference_block(references: list[dict]) -> str:
    if not references:
        return ""
    seen: set[tuple[str, str]] = set()
    lines = []
    for ref in references:
        key = (ref["memory_source"], ref["memory_target"])
        if key in seen:
            continue
        seen.add(key)
        lines.append(f'- "{ref["memory_source"]}" -> "{ref["memory_target"]}"')
    if not lines:
        return ""
    return (
        "Reference translations from the translation memory "
        "(reuse terminology/style where it genuinely fits, ignore otherwise):\n"
        + "\n".join(lines)
        + "\n\n"
    )


async def _translate_single(sentence: str, source_lang: str, target_lang: str) -> str:
    content = await ollama.chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Translate this sentence from {source_lang} to {target_lang}. "
                    f"Return only the translation, nothing else.\n\n{sentence}"
                ),
            },
        ]
    )
    return content.strip()


async def _translate_batch(
    sentences: list[str],
    references: list[dict],
    source_lang: str,
    target_lang: str,
) -> list[str]:
    if not sentences:
        return []

    numbered = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(sentences))
    user_prompt = (
        f"Translate the following numbered sentences from {source_lang} to {target_lang}. "
        "This is technical documentation.\n\n"
        f"{_build_reference_block(references)}"
        "Sentences:\n"
        f"{numbered}\n\n"
        "Return ONLY a numbered list of translations in the same order and numbering, "
        "one per line. Do not merge, split, skip, or renumber lines."
    )

    content = await ollama.chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    )
    parsed = _parse_numbered_response(content, len(sentences))
    if parsed is not None:
        return parsed

    # The model didn't follow the numbered format (rare, but local models
    # vary in instruction-following). Fall back to one call per sentence so a
    # single malformed batch can't lose the rest of the document.
    return [await _translate_single(s, source_lang, target_lang) for s in sentences]


async def translate_text(text: str, source_lang: str, target_lang: str) -> dict:
    paragraphs = split_paragraphs(text)
    flat: list[tuple[int, str]] = [
        (p_idx, sentence)
        for p_idx, paragraph in enumerate(paragraphs)
        for sentence in split_sentences(paragraph, source_lang)
    ]
    if not flat:
        return {"translated_text": "", "segments": []}

    sentences = [sentence for _, sentence in flat]
    embeddings = await ollama.embed(sentences)
    matches = [
        _best_match(vector_store.query(embedding, source_lang, target_lang, settings.top_k_matches))
        for embedding in embeddings
    ]

    translations: list[str | None] = [None] * len(flat)
    pending_indices = []
    for i, match in enumerate(matches):
        if match and match["type"] == "exact":
            translations[i] = match["memory_target"]
        else:
            pending_indices.append(i)

    for start in range(0, len(pending_indices), settings.batch_size):
        batch_indices = pending_indices[start : start + settings.batch_size]
        batch_sentences = [sentences[i] for i in batch_indices]
        batch_refs = [matches[i] for i in batch_indices if matches[i]]
        results = await _translate_batch(batch_sentences, batch_refs, source_lang, target_lang)
        for i, translation in zip(batch_indices, results):
            translations[i] = translation

    paragraph_groups: dict[int, list[str]] = {}
    segments = []
    for (p_idx, sentence), match, translation in zip(flat, matches, translations):
        paragraph_groups.setdefault(p_idx, []).append(translation or "")
        segments.append(
            {
                "source": sentence,
                "translation": translation or "",
                "paragraph_index": p_idx,
                "match": match,
            }
        )

    translated_text = "\n\n".join(" ".join(paragraph_groups[i]) for i in sorted(paragraph_groups))
    return {"translated_text": translated_text, "segments": segments}
