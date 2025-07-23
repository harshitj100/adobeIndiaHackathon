import fitz  # PyMuPDF
import spacy
import re

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")

def is_sentence_like(text):
    doc = nlp(text)
    has_subject = any(tok.dep_ in ("nsubj", "nsubjpass") for tok in doc)
    has_verb = any(tok.pos_ == "VERB" for tok in doc)
    return has_subject and has_verb

def spans_can_merge_by_y(span1, span2, y_tolerance=1.0):
    return abs(span1["origin"][1] - span2["origin"][1]) < y_tolerance

def spans_can_merge_by_font_and_x(span1, span2):
    return (
        span1["font"] == span2["font"] and
        span1["size"] == span2["size"] and
        span1["color"] == span2["color"] and
        span2["origin"][0] >= span1["origin"][0]
    )

def merge_spans(span1, span2, with_space=True):
    return {
        "text": span1["text"] + (" " if with_space else "") + span2["text"],
        "font": span1["font"],
        "size": span1["size"],
        "color": span1["color"],
        "origin": span1["origin"],
    }

def is_heading(span):
    font = span.get("font", "").lower()
    size = span.get("size", 0)
    text = span.get("text", "").strip()
    word_count = len(text.split())
    ends_with_colon = text.endswith(":")
    is_bold = "bold" in font or "black" in font

    # Reject very long sentences (usually paragraphs)
    if word_count > 12:
        return False

    # Common heading-like patterns
    structured_patterns = [
        r"^(appendix\s+[a-zA-Z0-9]+:?)",                       # Appendix B:
        r"^\d+(\.\d+)*\s+[A-Z][^\n]*$",                        # 1. Preamble, 2. Terms of Reference
        r"^\d+(\.\d+)*\s+[A-Z][a-z]+.*:*$",                    # 3.4 Public Libraries:
        r"^[A-Z][A-Za-z\s]+:$",                                # Phase II:
        r"^[A-Z][A-Za-z\s]+\s+[A-Z][A-Za-z\s]+:*$",            # Terms of Reference
    ]

    for pattern in structured_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return True

    # Accept bold short text with reasonable size
    if is_bold and word_count <= 8 and size >= 9.5:
        return True

    return False


def extract_pdf_info(pdf_path):
    doc = fitz.open(pdf_path)

    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("dict")["blocks"]
        final_spans = []

        for block in blocks:
            if "lines" not in block:
                continue

            raw_spans = []
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span.get("text", "").strip()
                    if text:
                        raw_spans.append(span)

            # Merge by Y
            y_merged_spans = []
            i = 0
            while i < len(raw_spans):
                current = raw_spans[i]
                while i + 1 < len(raw_spans) and spans_can_merge_by_y(current, raw_spans[i + 1]):
                    current = merge_spans(current, raw_spans[i + 1])
                    i += 1
                y_merged_spans.append(current)
                i += 1

            # Merge by font and X
            i = 0
            while i < len(y_merged_spans):
                current = y_merged_spans[i]
                while i + 1 < len(y_merged_spans) and spans_can_merge_by_font_and_x(current, y_merged_spans[i + 1]):
                    current = merge_spans(current, y_merged_spans[i + 1])
                    i += 1
                final_spans.append(current)
                i += 1

        # Only print headings
        for idx, span in enumerate(final_spans):
            if is_heading(span):
                font = span.get("font", "")
                size = span.get("size", 0)
                color = span.get("color", 0)
                x, y = span.get("origin", (0, 0))
                text = span.get("text", "")

                print("--------------------------------------------------")
                print(f"🟩 Text: {text}")
                print(f" Font Family: {font}")
                print(f" Font Style: {'bold' if 'bold' in font.lower() else 'normal'}")
                print(f" Size: {size}")
                print(f" Color: {color}")
                print(f" Indentation X: {x}")
                print(f" Indentation Y: {y}")
                print(f" Page: {page_num}, Merged Span: {idx}")
                print("--------------------------------------------------")

# 🔽 Replace with your actual file path
extract_pdf_info("file03-9.pdf") 