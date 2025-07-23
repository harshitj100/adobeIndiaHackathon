import fitz  # PyMuPDF
import spacy
import re

nlp = spacy.load("en_core_web_sm")

def is_sentence_like(text):
    doc = nlp(text)
    has_subject = any(tok.dep_ in ("nsubj", "nsubjpass") for tok in doc)
    has_verb = any(tok.pos_ == "VERB" for tok in doc)
    return has_subject and has_verb

def spans_can_merge_by_y(span1, span2, y_tolerance=1.0):
    return (
        abs(span1["origin"][1] - span2["origin"][1]) < y_tolerance and
        span1.get("block_id") == span2.get("block_id")
    )

def spans_can_merge_by_font_and_x(span1, span2):
    return (
        span1["font"] == span2["font"] and
        span1["size"] == span2["size"] and
        span1["color"] == span2["color"] and
        span2["origin"][0] >= span1["origin"][0] and
        span1.get("block_id") == span2.get("block_id")
    )

def merge_spans(span1, span2, with_space=True):
    return {
        "text": span1["text"] + (" " if with_space else "") + span2["text"],
        "font": span1["font"],
        "size": span1["size"],
        "color": span1["color"],
        "origin": span1["origin"],
        "block_id": span1["block_id"],
    }

def has_similar_font_properties(span1, span2):
    font1 = span1.get("font", "").lower()
    font2 = span2.get("font", "").lower()
    is_normal1 = not ("bold" in font1 or "black" in font1)
    is_normal2 = not ("bold" in font2 or "black" in font2)

    return (
        span1.get("font") == span2.get("font") and
        span1.get("size") == span2.get("size") and
        span1.get("color") == span2.get("color") and
        is_normal1 and is_normal2
    )

def is_heading(span):
    font = span.get("font", "").lower()
    size = span.get("size", 0)
    text = span.get("text", "").strip()
    word_count = len(text.split())
    ends_with_colon = text.endswith(":")
    is_bold = "bold" in font or "black" in font  # Detect bold from font name

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

    # Final heuristic: allow bold + size ≥ 11 + short text
    return (
        size >= 15 or
        (is_bold and size >= 11 and word_count <= 12) or
        (ends_with_colon and word_count <= 10)
    )

def extract_pdf_info(pdf_path):
    doc = fitz.open(pdf_path)

    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("dict")["blocks"]
        raw_spans = []

        for block_id, block in enumerate(blocks):
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span.get("text", "").strip()
                    if text:
                        span["block_id"] = block_id
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

        # Merge by font + X
        final_spans = []
        i = 0
        while i < len(y_merged_spans):
            current = y_merged_spans[i]
            while i + 1 < len(y_merged_spans) and spans_can_merge_by_font_and_x(current, y_merged_spans[i + 1]):
                current = merge_spans(current, y_merged_spans[i + 1])
                i += 1
            final_spans.append(current)
            i += 1

        # Detect headings
        skip_indices = set()
        for idx in range(len(final_spans) - 1):
            if has_similar_font_properties(final_spans[idx], final_spans[idx + 1]):
                skip_indices.add(idx)
                skip_indices.add(idx + 1)

        for idx, span in enumerate(final_spans):
            if idx in skip_indices:
                continue
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
extract_pdf_info("file02.pdf")
