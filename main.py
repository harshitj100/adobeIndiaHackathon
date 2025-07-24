# main.py

from core.extractor import extract_pdf_headings, extract_pdf_content
from logic.rank_sections import rank_relevant_sections, print_result

# 🔽 Full list of input documents
input_documents = [
    "South of France - Cities.pdf",
    "South of France - Cuisine.pdf",
    "South of France - History.pdf",
    "South of France - Restaurants and Hotels.pdf",
    "South of France - Things to Do.pdf",
    "South of France - Tips and Tricks.pdf",
    "South of France - Traditions and Culture.pdf"
]

# 👤 Persona and job prompt
persona = "Travel Planner"
job = "Plan a trip of 4 days for a group of 10 college friends."

# 🔧 Extract headings and content blocks from each PDF
def build_section_blocks(file_path):
    filename = file_path.split("/")[-1]
    headings = extract_pdf_headings(file_path)
    content_blocks = extract_pdf_content(file_path, headings)

    sections = []
    for block in content_blocks:
        sections.append({
            "document": filename,
            "heading": block["heading"],
            "content": block["content"],
            "page_start": block["page_start"],
            "page_end": block["page_end"],
        })
    return sections

if __name__ == "__main__":
    # 📄 Collect all sections across all PDFs
    all_sections = []
    for file_path in input_documents:
        all_sections.extend(build_section_blocks(file_path))

    # 🧠 Run semantic ranking based on persona and job
    metadata, top_sections = rank_relevant_sections(all_sections, persona, job)

    # 🖨️ Print the final results cleanly to terminal
    print_result(metadata, top_sections)
