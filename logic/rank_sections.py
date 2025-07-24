# logic/rank_sections.py

from sentence_transformers import SentenceTransformer
from torch.nn.functional import cosine_similarity
import torch
from datetime import datetime

def rank_relevant_sections(all_sections, persona, job, top_k=5):
    model = SentenceTransformer("intfloat/e5-base")

    # Step 1: Encode query
    query_text = f"query: {job}"
    query_embedding = model.encode(query_text, normalize_embeddings=True)
    query_tensor = torch.tensor([query_embedding])

    # Step 2: Score sections
    scored = []
    for section in all_sections:
        passage = f"passage: {section['content']}"
        section_embedding = model.encode(passage, normalize_embeddings=True)
        section_tensor = torch.tensor([section_embedding])
        score = cosine_similarity(query_tensor, section_tensor).item()

        scored.append({
            "document": section["document"],
            "section_title": section["heading"],
            "page_number": section["page_start"],
            "score": score,
            "refined_text": section["content"].strip()
        })

    # Step 3: Sort and select top sections
    scored.sort(key=lambda x: x["score"], reverse=True)
    top_sections = scored[:top_k]

    # Step 4: Create formatted output
    metadata = {
        "input_documents": list({s['document'] for s in all_sections}),
        "persona": persona,
        "job_to_be_done": job,
        "processing_timestamp": datetime.now().isoformat()
    }

    return metadata, top_sections

def print_result(metadata, top_sections):
    print("\n" + "=" * 100)
    print("🧠  Persona-Driven Document Intelligence Output")
    print("=" * 100)

    # Metadata Section
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
    for rank, section in enumerate(top_sections, 1):
        print(f"\n{rank}. Document: {section['document']}")
        print(f"   Section Title: {section['section_title']}")
        print(f"   Importance Rank: {rank}")
        print(f"   Page Number: {section['page_number']}")

    # Subsection Analysis
    print("\n📄 Subsection Analysis")
    print("------------------------")
    for section in top_sections:
        print(f"\n📘 Document: {section['document']}")
        print(f"📄 Page Number: {section['page_number']}")
        print(f"🔍 Refined Text:\n{section['refined_text']}\n")
        print("-" * 80)
