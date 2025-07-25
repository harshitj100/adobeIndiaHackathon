# logic/rank_sections.py

from sentence_transformers import SentenceTransformer
from torch.nn.functional import cosine_similarity
from datetime import datetime
import torch
import re

# ---------- Preprocessing Helpers ---------- #

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # collapse whitespace
    text = re.sub(r'•|▪|-', '', text)  # remove bullets
    return text.strip()

def is_irrelevant_heading(title):
    lowered = title.lower()
    return any([
        "table of contents" in lowered,
        "about" in lowered,
        "disclaimer" in lowered,
        "copyright" in lowered,
        len(title.split()) <= 1  # filter overly generic single words like "introduction"
    ])

# ---------- Main Logic ---------- #

def rank_relevant_sections(all_sections, persona, job, top_k=5):
    # 🧠 Load model
    model = SentenceTransformer("intfloat/e5-large")  # Best model within 1GB
    query_text = f"query: {job}"
    query_embedding = model.encode(query_text, normalize_embeddings=True)
    query_tensor = torch.tensor([query_embedding])

    scored = []

    for section in all_sections:
        title = section["heading"].strip()
        content = section["content"].strip()

        # ✂️ Filter bad sections
        if not title or not content:
            continue
        if is_irrelevant_heading(title):
            continue

        # 🧹 Preprocess content
        cleaned_text = clean_text(content)
        if len(cleaned_text.split()) < 30:
            continue  # too short to be useful

        # 🧠 Embed and score
        passage = f"passage: {cleaned_text}"
        section_embedding = model.encode(passage, normalize_embeddings=True)
        section_tensor = torch.tensor([section_embedding])
        score = cosine_similarity(query_tensor, section_tensor).item()

        scored.append({
            "document": section["document"],
            "section_title": title,
            "page_number": section["page_start"],
            "score": score,
            "refined_text": cleaned_text
        })

    # 🔢 Sort by score
    scored.sort(key=lambda x: x["score"], reverse=True)
    top_sections = scored[:top_k]

    metadata = {
        "input_documents": list({s['document'] for s in all_sections}),
        "persona": persona,
        "job_to_be_done": job,
        "processing_timestamp": datetime.now().isoformat()
    }

    return metadata, top_sections

# ---------- Print Output ---------- #

def print_result(metadata, top_sections):
    print("\n" + "=" * 100)
    print("🧠  Persona-Driven Document Intelligence Output")
    print("=" * 100)

    # Metadata
    print("\n📌 Metadata")
    print("-----------")
    print("Input Documents:")
    for doc in metadata["input_documents"]:
        print(f"  - {doc}")
    print(f"\nPersona: {metadata['persona']}")
    print(f"Job to be done: {metadata['job_to_be_done']}")
    print(f"Processing timestamp: {metadata['processing_timestamp']}")

    # Extracted Sections
    print("\n🏆 Extracted Sections")
    print("----------------------")
    for i, section in enumerate(top_sections, 1):
        print(f"\n{i}. Document: {section['document']}")
        print(f"   Section Title: {section['section_title']}")
        print(f"   Importance Rank: {i}")
        print(f"   Page Number: {section['page_number']}")

    # Subsection Analysis
    print("\n📄 Subsection Analysis")
    print("------------------------")
    for section in top_sections:
        print(f"\n📘 Document: {section['document']}")
        print(f"📄 Page Number: {section['page_number']}")

        refined_text = section["refined_text"]
        if len(refined_text) > 1200:
            refined_text = refined_text[:1200].strip() + "..."

        print(f"🔍 Refined Text:\n{refined_text}")
        print("-" * 80)
