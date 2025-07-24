import fitz
from utils.text_merge import (
    spans_can_merge_by_y, spans_can_merge_by_font_and_x, merge_spans
)
from utils.font_utils import has_similar_font_properties
from utils.heading_rules import is_heading

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
                # ✅ Skip if X-indentation is more than 200
                if span["origin"][0] > 200:
                    continue

                print("--------------------------------------------------")
                print(f"🟩 Text: {span['text']}")
                # print(f" Font: {span['font']}")
                # print(f" Style: {'bold' if 'bold' in span['font'].lower() else 'normal'}")
                # print(f" Size: {span['size']}")
                # print(f" Color: {span['color']}")
                # print(f" X: {span['origin'][0]}")
                # print(f" Y: {span['origin'][1]}")
                # print(f" Page: {page_num}, Span #: {idx}")
                print("--------------------------------------------------")
