import fitz
from utils.text_merge import (
    spans_can_merge_by_y, spans_can_merge_by_font_and_x, merge_spans
)
from utils.font_utils import has_similar_font_properties
from utils.heading_rules import is_heading

def extract_pdf_headings(pdf_path):
    doc = fitz.open(pdf_path)
    all_headings = []

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

        # Merge by Y-axis
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
                if span["origin"][0] > 200:
                    continue

                heading_data = {
                    "text": span["text"].strip(),
                    "page": page_num,
                    "y": span["origin"][1],
                    "span": span
                }
                all_headings.append(heading_data)

    return all_headings

def extract_pdf_content(file_path, headings):
    doc = fitz.open(file_path)

    # Sort headings by page and vertical position
    headings_sorted = sorted(headings, key=lambda h: (h["page"], h.get("y", 0)))

    # Add a dummy ending heading to capture the last section
    dummy_end = {"page": doc.page_count, "text": "END_OF_DOCUMENT", "y": float('inf')}
    headings_sorted.append(dummy_end)

    content_blocks = []

    for i in range(len(headings_sorted) - 1):
        current = headings_sorted[i]
        next_heading = headings_sorted[i + 1]

        content = []
        for page_num in range(current["page"], next_heading["page"] + 1):
            page = doc.load_page(page_num - 1)
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        y = span["origin"][1]

                        if page_num == current["page"] and y <= current.get("y", 0):
                            continue  # skip text before current heading
                        if page_num == next_heading["page"] and y >= next_heading.get("y", float("inf")):
                            continue  # skip text after next heading

                        content.append(span["text"])

        content_blocks.append({
            "heading": current["text"],
            "content": " ".join(content).strip(),
            "page_start": current["page"],
            "page_end": next_heading["page"]
        })

    return content_blocks
