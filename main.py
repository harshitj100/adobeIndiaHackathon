# main.py
from core.extractor import extract_pdf_headings, extract_pdf_content

if __name__ == "__main__":
    file_path = "file03.pdf"

    # Step 1: Extract headings
    headings = extract_pdf_headings(file_path)
    for h in headings:
        print(f"{h['page']:>2}: {h['text']}")

    # Step 2: Extract content between headings
    # content_blocks = extract_pdf_content(file_path, headings)
    # for block in content_blocks:
    #     print(f"\n🔷 Heading: {block['heading']}")
    #     print(f"📄 Pages: {block['page_start']} to {block['page_end']}")
    #     print(f"📝 Content:\n{block['content']}")
