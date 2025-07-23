import fitz  # PyMuPDF
import re

def normalize_font_family(font_name):
    font_name = font_name.lower()
    font_name = re.sub(r'(mt|psmt|bold|italic|regular|medium|light|semibold)', '', font_name)
    font_name = re.sub(r'[^a-z]', '', font_name)
    return font_name

pdf_path = "file03-2.pdf"
doc = fitz.open(pdf_path)

print(f"Number of pages: {len(doc)}\n")

for page_number, page in enumerate(doc, start=1):
    print(f"\n--- Page {page_number} ---\n")
    
    blocks = page.get_text("dict")["blocks"]
    
    for block_index, block in enumerate(blocks):
        if "lines" not in block:
            continue

        # Flatten spans in block
        all_spans = []
        for line in block["lines"]:
            all_spans.extend(line["spans"])

        merged_spans = []
        prev_span = None

        for span_index, span in enumerate(all_spans):
            text = span["text"]
            raw_font = span["font"]
            font_family = normalize_font_family(raw_font)
            size = span["size"]
            color = span.get("color", 0)

            if prev_span is None:
                prev_span = {
                    "text": text,
                    "font_family": font_family,
                    "size": size,
                    "color": color
                }
            else:
                if (
                    font_family == prev_span["font_family"]
                    and abs(size - prev_span["size"]) < 0.01
                ):
                    prev_span["text"] += " " + text
                else:
                    merged_spans.append(prev_span)
                    prev_span = {
                        "text": text,
                        "font_family": font_family,
                        "size": size,
                        "color": color
                    }

        if prev_span:
            merged_spans.append(prev_span)

        # Print result
        for i, span in enumerate(merged_spans):
            print(f"Merged Text: {span['text']}")
            print(f" Font Family: {span['font_family']}")
            print(f" Size: {span['size']}")
            print(f" Color: {span['color']}")
            print(f" Page: {page_number}, Block: {block_index}, Merged Span: {i}")
            print("-" * 50)

doc.close()
