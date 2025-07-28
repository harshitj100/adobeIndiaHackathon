# main.py
import fitz
import time
from core.extractor import extract_pdf_headings, extract_pdf_content
#from sentence_transformers import SentenceTransformer, util

import json
import os
from pathlib import Path





def classify_and_print_headings(headings):
    # Define font strength hierarchy (modify as needed)
    font_strength = {
        "Arial-Black": 5,
        "Arial-BoldMT": 4,
        "Arial-BoldItalicMT": 3,
        "Arial-ItalicMT": 2,
        "ArialMT": 1
    }
    process_front_page = should_include_front_page(headings)


    stack = []

    for heading in headings:

        if not process_front_page and heading.get('page', 0) == 1:
            continue
        if heading.get('size', 0) > 15:
            heading['level'] = 1
            stack = [heading]  
            continue

        while stack:
            top = stack[-1]
            top_size = top.get('size', 0)
            curr_size = heading.get('size', 0)

            if top_size > curr_size:
                heading['level'] = top.get('level', 0) + 1
                break
            elif top_size == curr_size:
                top_str = font_strength.get(top.get('font'), 0)
                curr_str = font_strength.get(heading.get('font'), 0)

                if top_str > curr_str:
                    heading['level'] = top.get('level', 0) + 1
                    break
                elif top_str == curr_str:
                    if heading.get('y', 0) < top.get('y', 0):
                        stack.pop()
                        continue
                    else:
                        heading['level'] = top.get('level', 1)
                        stack.pop()
                        break
                else:
                    stack.pop()
            else:
                stack.pop()

        if not stack:
            heading['level'] = 1

        stack.append(heading)

    # Print final results
    print("\nDocument Structure:\n")
    for heading in headings:
        if 'level' not in heading:
            continue

        indent = '    ' * (heading['level'] - 1)
        print(f"{indent}L{heading['level']}: {heading.get('text', '')}")
        print(f"{indent}   Page: {heading.get('page', '?')}, Size: {heading.get('size', '?')}")
        print(f"{indent}   Font: {heading.get('font', '?')}")
        print("-" * 60)


def extract_pdf_title(pdf_path):
    """Extract title from first page by finding largest consecutive text blocks with similar styling."""
    doc = fitz.open(pdf_path)
    page = doc[0]

    # Get text blocks with full formatting information
    blocks = page.get_text("dict")["blocks"]

    # Filter and score potential title blocks
    candidates = []
    current_group = []

    for block in blocks:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                # Skip small text (likely body text or page numbers)
                if span["size"] < 16:  # Minimum title font size threshold
                    continue

                # Group consecutive blocks with similar styling
                if (current_group and
                        abs(span["size"] - current_group[-1]["size"]) < 2 and
                        span["font"] == current_group[-1]["font"] and
                        span["color"] == current_group[-1]["color"]):
                    current_group.append(span)
                else:
                    if current_group:
                        candidates.append(current_group)
                    current_group = [span]

    if current_group:  # Add the last group
        candidates.append(current_group)

    if not candidates:
        return None

    # Find the group with largest average font size
    best_group = max(candidates, key=lambda group: sum(s["size"] for s in group) / len(group))

    # Combine text from all spans in the best group
    title = " ".join(span["text"].strip() for span in best_group)
    title = " ".join(title.split())  # Normalize whitespace

    # Additional verification (optional)
    bbox = fitz.Rect(best_group[0]["bbox"])
    if bbox.y0 > page.rect.height * 0.3:  # Not in top 30% of page
        return None

    doc.close()
    return title if title else None


def should_include_front_page(headings):
    """
    Determines if front page should be included in structure analysis based on:
    1. Number of headings on front page (page 1)
    2. Positioning of headings
    3. Total page count

    Returns: True if front page should be included, False otherwise
    """
    if not headings:
        return False

    # Count total pages by finding max page number
    total_pages = max(h.get('page', 0) for h in headings)

    # Get all front page (page 1) headings
    front_page_headings = [h for h in headings if h.get('page') == 1]

    # Case 1: Single-page document - always include
    if total_pages == 1:
        return True

    # Case 2: Front page has insufficient content (1-2 headings)
    if len(front_page_headings) <= 2:
        return False

    # Case 3: Check if front page headings are positioned like titles
    y_positions = [h.get('y', 0) for h in front_page_headings]
    avg_y = sum(y_positions) / len(y_positions) if y_positions else 0

    # If most headings are in top half of page, likely a title page
    if avg_y < 300:  # Adjust threshold based on typical page height
        return False

    # Default case: Include front page
    return True


def process_pdf_to_json(pdf_path):
    """
    Process a PDF file and save heading structure in specified JSON format
    Returns: Path to saved JSON file or None if failed
    """
    try:
        # Create outputs directory if not exists (with full permissions)
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True, mode=0o777)

        # Generate output filename
        pdf_name = Path(pdf_path).stem
        json_path = output_dir / f"{pdf_name}_outline.json"

        # Verify PDF exists
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Extract and classify headings
        headings = classify_and_print_headings(extract_pdf_headings(pdf_path))

        # Prepare JSON in specified format
        result = {
            "title": "Sample Document Title",  # Replace with your title extraction
            "outline": [
                {
                    "level": f"H{heading['level']}",
                    "text": heading.get('text', '').strip(),
                    "page": heading.get('page', 1) - 1  # Converting to 0-based index
                }
                for heading in headings
            ]
        }

        # Save to JSON with verification
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        # Verify file was created
        if not json_path.exists():
            raise IOError(f"Failed to create JSON file at {json_path}")

        print(f"Successfully created: {json_path}")
        return json_path

    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")
        return None


if __name__ == "__main__":
    files=["South of France - Cuisine.pdf","South of France - History.pdf","South of France - Restaurants and Hotels.pdf","South of France - Tips and Tricks.pdf","South of France - Traditions and Culture.pdf"]
    files2=["file01.pdf","file02.pdf","file03.pdf"]
    start_time = time.time()
    for file_path in files2:

        try:
            output_path = process_pdf_to_json(file_path)
            print(f"Successfully processed: {output_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
        # for i, h in enumerate(headings, start=1):
        #     print(f"   {h['text']}")



    elapsed = time.time() - start_time
    print(f"Execution time: {elapsed:.4f} seconds")
    # Step 2: Define your headings (order preserved as they appear in the PDF)


    # Step 3: Embed all headings into semantic vectors

    #print_headings_with_levels(sorted_headings)

    # Step 2: Print heading details
    # print("📘 Extracted Headings with Properties:\n")
    # for i, h in enumerate(headings, start=1):
    #     print(f"🔹 Heading {i}")
    #     for key, value in h.items():
    #         print(f"   {key}: {value}")
    #     print("-" * 60)

    # Optional Step 3: Extract and print content between headings
    # content_blocks = extract_pdf_content(file_path, headings)
    # for block in content_blocks:
    #     print(f"\n🔷 Heading: {block['heading']}")
    #     print(f"📄 Pages: {block['page_start']} to {block['page_end']}")
    #     print(f"📝 Content:\n{block['content']}")