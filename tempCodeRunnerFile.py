import fitz  # PyMuPDF
import spacy
import re

# -------------------- Load spaCy --------------------
print("🔄 Loading spaCy model...")
nlp = spacy.load("en_core_web_sm")
print("✅ spaCy model loaded.\n")

# -------------------- Helper Functions --------------------
def is_sentence_like(text):
    print(f"\n🔍 Checking if text is sentence-like: \"{text}\"")
    doc = nlp(text)
    has_subject = any(tok.dep_ in ("nsubj", "nsubjpass") for tok in doc)
    has_verb = any(tok.pos_ == "VERB" for tok in doc)
    print(f"➡️  Has subject: {has_subject}, Has verb: {has_verb}")
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
    merged_text = span1["text"] + (" " if with_space else "") + span2["text"]
    print(f"🧩 Merging spans: \"{span1['text']}\" + \"{span2['text']}\" => \"{merged_text}\"")
    return {
        "text": merged_text,
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
    text = span.get("text", "").strip()
    font = span.get("font", "").lower()
    size = span.get("size", 0)
    word_count = len(text.split())
    ends_with_colon = text.endswith(":")
    is_bold = "bold" in font or "black" in font

    print(f"\n📌 Checking heading for span: \"{text}\"")
    print(f"    ↪ Font: {font}, Size: {size}, Word Count: {word_count}, Ends with ':': {ends_with_colon}, Bold: {is_bold}")

    structured_heading_pattern = r"^[A-Z][a-zA-Z]+\s+[A-Z0-9]+:\s?.+"
    if re.match(structured_heading_pattern, text):
        print("    ✅ Matched structured heading pattern")
        return True

    numbered_heading_pattern = r"^\d+(\.\d+)*\.?\s+[A-Z]"
    if re.match(numbered_heading_pattern, text) and word_count <= 10:
        print("    ✅ Matched numbered heading pattern")
        return True

    if ends_with_colon:
        if word_count > 10:
            print("    ❌ Too many words with colon")
            return False
        if is_sentence_like(text) and not is_bold:
            print("    ❌ Looks like a sentence (not bold)")
            return False

    result = (
        size >= 15 or
        (is_bold and size >= 11 and word_count <= 12) or
        (ends_with_colon and word_count <= 10)
    )
    print("    ✅ Heading Detected" if result else "    ❌ Not a Heading")
    return result

# -------------------- Main PDF Extraction --------------------
def extract_pdf_info(pdf_path):
    print(f"📄 Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)

    for page_num, page in enumerate(doc, start=1):
        print(f"\n\n==================== 📄 PAGE {page_num} ====================")

        # -------------------- Extract Spans --------------------
        blocks = page.get_text("dict")["blocks"]
        raw_spans = []

        print("🔍 Extracting raw spans from blocks...\n")
        for block_id, block in enumerate(blocks):
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span.get("text", "").strip()
                    if text:
                        span["block_id"] = block_id
                        raw_spans.append(span)
                        print(f"   📦 Raw Span: \"{text}\" (Font: {span['font']}, Size: {span['size']})")

        # -------------------- Merge Spans by Y --------------------
        print("\n🔗 Merging spans by vertical (Y) alignment...\n")
        y_merged_spans = []
        i = 0
        while i < len(raw_spans):
            current = raw_spans[i]
            while i + 1 < len(raw_spans) and spans_can_merge_by_y(current, raw_spans[i + 1]):
                current = merge_spans(current, raw_spans[i + 1])
                i += 1
            y_merged_spans.append(current)
            i += 1

        # -------------------- Merge Spans by Font + X --------------------
        print("\n🔗 Merging spans by font + horizontal (X) alignment...\n")
        final_spans = []
        i = 0
        while i < len(y_merged_spans):
            current = y_merged_spans[i]
            while i + 1 < len(y_merged_spans) and spans_can_merge_by_font_and_x(current, y_merged_spans[i + 1]):
                current = merge_spans(current, y_merged_spans[i + 1])
                i += 1
            final_spans.append(current)
            i += 1

        # -------------------- Mark Spans to Skip --------------------
        print("\n🧠 Identifying similar font spans to skip...\n")
        skip_indices = set()
        for idx in range(len(final_spans) - 1):
            if has_similar_font_properties(final_spans[idx], final_spans[idx + 1]):
                skip_indices.add(idx)
                skip_indices.add(idx + 1)
                print(f"   ⏭️  Skipping spans #{idx} and #{idx+1} due to similar normal font properties.")

        # -------------------- Detect Headings --------------------
        print("\n🎯 Detecting headings from final spans...\n")
        for idx, span in enumerate(final_spans):
            if idx in skip_indices:
                print(f"   ⏭️  Skipping span #{idx} from heading check.")
                continue
            if is_heading(span):
                font = span.get("font", "")
                size = span.get("size", 0)
                color = span.get("color", 0)
                x, y = span.get("origin", (0, 0))
                text = span.get("text", "")

                print("\n✅ Detected Heading:")
                print("--------------------------------------------------")
                print(f" Page Number      : {page_num}")
                print(f" Merged Span Index: {idx}")
                print(f" Text             : {text}")
                print(f" Font Family      : {font}")
                print(f" Font Style       : {'bold' if 'bold' in font.lower() else 'normal'}")
                print(f" Font Size        : {size}")
                print(f" Font Color       : {color}")
                print(f" Indentation X    : {x}")
                print(f" Indentation Y    : {y}")
                print("--------------------------------------------------")

# 🔽 Replace with your actual file path
extract_pdf_info("file02.pdf")
