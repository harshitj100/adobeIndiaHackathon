import fitz  # PyMuPDF
import spacy
import re

nlp = spacy.load("en_core_web_sm")

def is_sentence_like(text):
    doc = nlp(text)
    has_subject = any(tok.dep_ in ("nsubj", "nsubjpass") for tok in doc)
    has_verb = any(tok.pos_ == "VERB" for tok in doc)
    return has_subject and has_verb

def font_base(font_name):
    return font_name.lower().split(",")[0]  # e.g., 'arial' from 'Arial,Bold'

def spans_can_merge_by_y_and_font(span1, span2, y_tolerance=1.0):
    return (
        abs(span1["origin"][1] - span2["origin"][1]) < y_tolerance or
        span1.get("block_id") == span2.get("block_id") and
        font_base(span1["font"]) == font_base(span2["font"]) and
        span1["size"] == span2["size"] and
        span1["color"] == span2["color"]
    )

def merge_spans(span1, span2, with_space=True):
    return {
        "text": span1["text"] + (" " if with_space else "") + span2["text"],
        "font": span2["font"] if span1["font"] == "Symbol" else span1["font"],
        "size": span2["size"] if span1["font"] == "Symbol" else span1["size"],
        "color": span2["color"] if span1["font"] == "Symbol" else span1["color"],
        "origin": span1["origin"],
        "block_id": span1["block_id"],
    }

def has_similar_font_properties(span1, span2):
    return (
        font_base(span1.get("font", "")) == font_base(span2.get("font", "")) and
        abs(span1.get("size", 0) - span2.get("size", 0)) < 0.5 and
        span1.get("color") == span2.get("color")
    )

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

        # Merge spans and handle Symbol font
        merged_spans = []
        i = 0
        while i < len(raw_spans):
            current = raw_spans[i]

            # Merge Symbol bullet with next
            if current["font"] == "Symbol" and i + 1 < len(raw_spans):
                current = merge_spans(current, raw_spans[i + 1])
                i += 1

            while i + 1 < len(raw_spans) and spans_can_merge_by_y_and_font(current, raw_spans[i + 1]):
                current = merge_spans(current, raw_spans[i + 1])
                i += 1

            merged_spans.append(current)
            i += 1

        print(f"\n========== 📄 PAGE {page_num} - RAW TEXT SPANS ==========\n")
        for idx, span in enumerate(merged_spans):
            font = span.get("font", "")
            size = span.get("size", 0)
            color = span.get("color", 0)
            x, y = span.get("origin", (0, 0))
            text = span.get("text", "")
            print(f"[{idx}] Text: {text}")
            # print(f"     Font Family: {font}")
            # print(f"     Font Style: {'bold' if 'bold' in font.lower() else 'normal'}")
            # print(f"     Size: {size}, Color: {color}")
            # print(f"     Indent X: {x}, Indent Y: {y}")
            print()

        # Detect headings first
        headings = []
        skip_indices = set()
        for idx in range(len(merged_spans) - 1):
            if has_similar_font_properties(merged_spans[idx], merged_spans[idx + 1]):
                skip_indices.add(idx)
                skip_indices.add(idx + 1)

        for idx, span in enumerate(merged_spans):
            if idx in skip_indices:
                continue
            if is_heading(span):
                headings.append((idx, span))

        # Merge multi-line headings
        merged_headings = []
        i = 0
        while i < len(headings):
            idx1, span1 = headings[i]
            merged = span1.copy()
            j = i + 1
            while j < len(headings):
                idx2, span2 = headings[j]
                y_gap = abs(span2["origin"][1] - merged["origin"][1])
                same_size = abs(merged["size"] - span2["size"]) < 0.5
                same_font = font_base(merged["font"]) == font_base(span2["font"])

                if same_size and same_font and y_gap < 25:
                    merged["text"] += " " + span2["text"]
                    j += 1
                else:
                    break
            merged_headings.append(merged)
            i = j

        print(f"\n========== 🧭 PAGE {page_num} - MERGED HEADINGS ==========\n")
        for i, span in enumerate(merged_headings):
            font = span.get("font", "")
            size = span.get("size", 0)
            color = span.get("color", 0)
            x, y = span.get("origin", (0, 0))
            text = span.get("text", "")
            print(f"[{i}] 🟩 Heading: {text}")
            # print(f"     Font Family: {font}")
            # print(f"     Font Style: {'bold' if 'bold' in font.lower() else 'normal'}")
            # print(f"     Size: {size}, Color: {color}")
            # print(f"     Indent X: {x}, Indent Y: {y}")
            print()

# 🔽 Replace with your actual file path
extract_pdf_info("file03.pdf")
