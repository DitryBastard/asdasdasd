"""Lightweight automated QA checks on a translated segment.

These are deliberately conservative (few, high-confidence checks) rather
than an exhaustive linguistic QA suite: the goal is to catch the failure
modes that matter most for technical documentation - a dropped or altered
number, a segment the model didn't actually translate - without drowning
real, correct translations in false-positive warnings.
"""

import re

_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
_ALPHABETIC_RUN = re.compile(r"[A-Za-zА-Яа-яЁё]{4,}")


def _normalized_numbers(text: str) -> set[str]:
    # "178.29" and "178,29" are the same number under different decimal
    # separator conventions (common between en and ru source material) -
    # strip the separators so both compare equal, but keep grouped digits
    # distinct from ungrouped ones ("1000" vs "1,000" still normalize the
    # same way here, which is intentional: this check is about numeric
    # *content* going missing or changing, not formatting style).
    return {re.sub(r"[.,]", "", match) for match in _NUMBER.findall(text)}


def check_segment(source: str, translation: str) -> list[str]:
    """Returns human-readable (Russian) warning strings, empty if clean."""
    warnings: list[str] = []
    translation = translation.strip()
    source = source.strip()

    if not translation:
        warnings.append("Пустой перевод")
        return warnings

    if source and translation == source and _ALPHABETIC_RUN.search(source):
        warnings.append("Перевод дословно совпадает с оригиналом")

    source_numbers = _normalized_numbers(source)
    translation_numbers = _normalized_numbers(translation)
    if source_numbers != translation_numbers:
        warnings.append("Числа в переводе не совпадают с оригиналом")

    return warnings
