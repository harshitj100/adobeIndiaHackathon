# Adobe Challenge Round 1B: Persona-Driven Document Intelligence

## Overview
This solution provides a generic document intelligence system that extracts and ranks document sections based on a specific persona and their job-to-be-done.

## Approach

### 1. PDF Content Extraction
- Uses PyMuPDF to extract text with formatting information
- Classifies text blocks as headings or content based on:
  - Font size and formatting (bold, size)
  - Text patterns (capitalization, numbering)
  - Content structure analysis

### 2. Generic Keyword Extraction
- Extracts relevant keywords from persona and job description
- Identifies numbers, time periods, and domain-specific terms
- Uses stop-word filtering for better relevance

### 3. Relevance Scoring Algorithm
- **Persona Keywords (2x weight)**: Matches persona-related terms
- **Job Keywords (3x weight)**: Matches task-specific requirements
- **Title Boost**: Higher scores for matches in section titles
- **Domain Patterns**: Recognizes research, business, education, and technical domains
- **Content Length**: Bonus for comprehensive sections

### 4. Section Ranking and Extraction
- Scores all sections based on relevance to persona and job
- Ranks sections by importance
- Extracts subsections from top-ranked sections for detailed analysis

## Libraries Used
- **PyMuPDF (fitz)**: PDF text extraction with formatting preservation
- **json**: Data parsing and output formatting
- **re**: Pattern matching for text analysis
- **datetime**: Timestamp generation

## Key Features
- **Domain Agnostic**: Works with any type of document and persona
- **Lightweight**: No ML models, fast processing
- **Robust**: Handles various PDF formats and structures
- **Scalable**: Efficient processing of multiple documents

## Build and Run

```bash
# Build the Docker image
docker build --platform linux/amd64 -t document-intelligence:latest .

# Run the solution
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none \
  document-intelligence:latest