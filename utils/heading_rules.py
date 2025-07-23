import re
from nlp.sentence_detector import is_sentence_like

def is_heading(span):
    font = span.get("font", "").lower()
    size = span.get("size", 0)
    text = span.get("text", "").strip()
    word_count = len(text.split())
    ends_with_colon = text.endswith(":")
    is_bold = "bold" in font or "black" in font

    structured_heading_pattern = r"^[A-Z][a-zA-Z]+\s+[A-Z0-9]+:\s?.+"
    if re.match(structured_heading_pattern, text):
        return True

    numbered_heading_pattern = r"^\d+(\.\d+)*\.?\s+[A-Z]"
    if re.match(numbered_heading_pattern, text) and word_count <= 10:
        return True

    if ends_with_colon:
        if word_count > 10:
            return False
        if is_sentence_like(text) and not is_bold:
            return False

    return (
        size >= 15 or
        (is_bold and size >= 11 and word_count <= 12) or
        (ends_with_colon and word_count <= 10)
    )
