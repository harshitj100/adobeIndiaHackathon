import json
import os
import re
import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import logging

# Logging config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================
# Data Classes
# ======================

@dataclass
class DocumentSection:
    document: str
    page_number: int
    section_title: str
    content: str
    importance_rank: int = 0

@dataclass
class SubSection:
    document: str
    section_title: str
    refined_text: str
    page_number: int

# ======================
# Main Class
# ======================

class GenericDocumentIntelligence:
    def __init__(self):
        self.processed_documents = []
        self.all_sections = []

    def load_input_json(self, input_path: str) -> Dict[str, Any]:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading input file: {e}")
            raise

    def extract_pdf_content(self, pdf_path: str) -> List[Dict[str, Any]]:
        try:
            doc = fitz.open(pdf_path)
            sections = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("dict")

                for block in blocks["blocks"]:
                    if "lines" not in block:
                        continue

                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if not text or len(text) < 3:
                                continue

                            font_size = span["size"]
                            font_flags = span["flags"]
                            is_bold = bool(font_flags & 2**4)

                            section_info = self._classify_text_block(text, font_size, is_bold, page_num + 1)
                            if section_info:
                                sections.append(section_info)

            doc.close()
            return self._merge_and_clean_sections(sections)

        except Exception as e:
            logger.error(f"Error extracting from {pdf_path}: {e}")
            return []

    def _classify_text_block(self, text: str, font_size: float, is_bold: bool, page_num: int) -> Optional[Dict[str, Any]]:
        if len(text) < 5 or text.isdigit():
            return None

        heading_patterns = [r'^[A-Z][A-Za-z\s]+$', r'^\d+\.?\s+[A-Z]', r'^[IVX]+\.?\s+[A-Z]', r'^[A-Z]{2,}']
        content_indicators = [r'\.\s+[A-Z]', r',\s+', r';\s+']

        is_likely_heading = any(re.match(p, text) for p in heading_patterns) or font_size > 12 or is_bold
        if any(re.search(p, text) for p in content_indicators):
            is_likely_heading = False

        section_type = f"H{self._determine_heading_level(text, font_size, is_bold)}" if is_likely_heading else "content"

        return {
            "type": section_type,
            "text": text,
            "page": page_num,
            "font_size": font_size,
            "is_bold": is_bold
        }

    def _determine_heading_level(self, text: str, font_size: float, is_bold: bool) -> int:
        if font_size > 16 or text.isupper() or re.match(r'^\d+\.\s+[A-Z]', text):
            return 1
        elif font_size > 14 or is_bold or re.match(r'^[A-Z]\.\s+[A-Z]', text):
            return 2
        else:
            return 3

    def _merge_and_clean_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned = []
        current_section = None

        for section in sections:
            if section["type"].startswith("H"):
                if current_section:
                    cleaned.append(current_section)
                current_section = {
                    "section_title": section["text"],
                    "content": "",
                    "page": section["page"],
                    "level": section["type"]
                }
            elif section["type"] == "content" and current_section:
                if current_section["content"]:
                    current_section["content"] += " "
                current_section["content"] += section["text"]

        if current_section:
            cleaned.append(current_section)
        return cleaned

    def extract_keywords_from_context(self, persona: str, job_description: str) -> Dict[str, List[str]]:
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                      'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
                      'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}

        def extract_words(text, min_len=3):
            return [w for w in re.findall(r'\b[a-zA-Z]{' + str(min_len) + r',}\b', text.lower()) if w not in stop_words]

        return {
            "persona_keywords": extract_words(persona)[:10],
            "job_keywords": extract_words(job_description)[:15],
            "numbers": re.findall(r'\d+', job_description),
            "time_periods": re.findall(r'\b\d+\s*(?:day|days|week|weeks|month|months|year|years)\b', job_description)
        }

    def calculate_section_relevance(self, section, keywords, persona, job_description):
        title = section.get("section_title", "").lower()
        content = section.get("content", "").lower()
        combined = f"{title} {content}"

        score = 0
        score += sum(kw in combined for kw in keywords["persona_keywords"]) * 2.0
        score += sum(kw in combined for kw in keywords["job_keywords"]) * 3.0
        score += sum(kw in title for kw in keywords["persona_keywords"]) * 1.5
        score += sum(kw in title for kw in keywords["job_keywords"]) * 2.0
        score += sum(num in combined for num in keywords["numbers"]) * 1.5
        score += sum(tp in combined for tp in keywords["time_periods"]) * 1.0
        if len(content.split()) > 50:
            score += min(2.0, len(content.split()) / 100)

        return round(score, 2)

    def rank_sections(self, sections, persona, job_description, top_n=10):
        keywords = self.extract_keywords_from_context(persona, job_description)
        scored = [
            {
                "section": s,
                "score": self.calculate_section_relevance(s, keywords, persona, job_description)
            } for s in sections
        ]
        scored.sort(key=lambda x: x["score"], reverse=True)

        return [
            DocumentSection(
                document=s["section"].get("document", "unknown"),
                page_number=s["section"].get("page", 1),
                section_title=s["section"].get("section_title", ""),
                content=s["section"].get("content", ""),
                importance_rank=i + 1
            )
            for i, s in enumerate(scored[:top_n])
        ]

    def extract_subsections(self, sections: List[DocumentSection], max_subsections=20) -> List[SubSection]:
        subsections = []
        for section in sections[:5]:
            sentences = re.split(r'[.!?]+', section.content)
            for i in range(0, len(sentences), 3):
                chunk = ' '.join(sentences[i:i + 3]).strip()
                if len(chunk) > 50:
                    refined = self._refine_text(chunk)
                    subsections.append(SubSection(
                        document=section.document,
                        section_title=section.section_title,
                        refined_text=refined,
                        page_number=section.page_number
                    ))
                    if len(subsections) >= max_subsections:
                        break
            if len(subsections) >= max_subsections:
                break
        return subsections

    def _refine_text(self, text):
        text = ' '.join(text.split())
        if text and not text.endswith(('.', '!', '?')):
            last = max(text.rfind('.'), text.rfind('!'), text.rfind('?'))
            if last > len(text) * 0.7:
                text = text[:last + 1]
        return text[0].upper() + text[1:] if text else text

    def process_documents(self, input_dir: str, output_dir: str):
        input_json_path = os.path.join(input_dir, "input.json")
        if not os.path.exists(input_json_path):
            raise FileNotFoundError(f"Input JSON not found at {input_json_path}")

        input_data = self.load_input_json(input_json_path)
        persona = input_data.get("persona", {}).get("role", "")
        job = input_data.get("job_to_be_done", {}).get("task", "")
        docs = input_data.get("documents", [])

        all_sections = []
        for doc in docs:
            fname = doc.get("filename", "")
            if not fname:
                continue
            fpath = os.path.join(input_dir, fname)
            if not os.path.exists(fpath):
                logger.warning(f"Missing file: {fpath}")
                continue

            sections = self.extract_pdf_content(fpath)
            for s in sections:
                s["document"] = fname
            all_sections.extend(sections)

        ranked = self.rank_sections(all_sections, persona, job)
        subs = self.extract_subsections(ranked)

        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, "output.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "input_documents": [d["filename"] for d in docs],
                    "persona": persona,
                    "job_to_be_done": job,
                    "processing_timestamp": datetime.now().isoformat()
                },
                "extracted_sections": [
                    {
                        "document": s.document,
                        "page_number": s.page_number,
                        "section_title": s.section_title,
                        "importance_rank": s.importance_rank
                    } for s in ranked
                ],
                "sub_section_analysis": [
                    {
                        "document": s.document,
                        "section_title": s.section_title,
                        "refined_text": s.refined_text,
                        "page_number": s.page_number
                    } for s in subs
                ]
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved output to {out_path}")
