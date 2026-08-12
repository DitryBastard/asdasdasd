"""TMX (Translation Memory eXchange) 1.4b import/export.

TMX is the industry-standard XML interchange format for translation
memories. Exporting to it means the memory built here isn't a data silo -
it can be opened, backed up, or migrated with any mainstream CAT tool
(Trados, memoQ, OmegaT, ...); importing lets an existing memory from one of
those tools seed this one instead of starting from zero.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom

_XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def build_tmx(entries: list[dict]) -> bytes:
    """entries: list of {source_text, target_text, source_lang, target_lang}."""
    tmx = ET.Element("tmx", version="1.4")
    ET.SubElement(
        tmx,
        "header",
        {
            "creationtool": "AI Translator",
            "creationtoolversion": "1.0",
            "datatype": "plaintext",
            "segtype": "sentence",
            "adminlang": "en",
            "srclang": entries[0]["source_lang"] if entries else "*all*",
            "o-tmf": "AI Translator",
        },
    )
    body = ET.SubElement(tmx, "body")
    for entry in entries:
        tu = ET.SubElement(body, "tu")
        source_tuv = ET.SubElement(tu, "tuv", {_XML_LANG: entry["source_lang"]})
        ET.SubElement(source_tuv, "seg").text = entry["source_text"]
        target_tuv = ET.SubElement(tu, "tuv", {_XML_LANG: entry["target_lang"]})
        ET.SubElement(target_tuv, "seg").text = entry["target_text"]

    raw = ET.tostring(tmx, encoding="utf-8")
    return minidom.parseString(raw).toprettyxml(indent="  ", encoding="utf-8")


def _normalize_lang(lang: str) -> str:
    # TMX language tags vary in casing/region ("en-US", "RU", "ru-RU") -
    # match on the primary subtag only so "en" matches "en-GB", etc.
    return lang.strip().lower().split("-")[0]


def parse_tmx(data: bytes, source_lang: str, target_lang: str) -> list[dict]:
    """Extract (source_text, target_text) pairs for one language pair from a
    TMX file. A <tu> may carry more than two <tuv> (a multilingual memory);
    only the ones matching source_lang/target_lang are used.
    """
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError("Не удалось прочитать TMX — файл повреждён или не является TMX.") from exc

    wanted_source = _normalize_lang(source_lang)
    wanted_target = _normalize_lang(target_lang)

    pairs: list[dict] = []
    for tu in root.iter("tu"):
        texts: dict[str, str] = {}
        for tuv in tu.findall("tuv"):
            lang = tuv.get(_XML_LANG) or tuv.get("lang")
            seg = tuv.find("seg")
            if lang and seg is not None and seg.text:
                texts[_normalize_lang(lang)] = seg.text
        source_text = texts.get(wanted_source)
        target_text = texts.get(wanted_target)
        if source_text and target_text:
            pairs.append({"source_text": source_text, "target_text": target_text})
    return pairs
