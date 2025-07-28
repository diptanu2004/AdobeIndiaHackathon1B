# Adobe Hackathon Round 1B: Persona-Driven Document Intelligence

## Project Overview

This solution implements an intelligent document analysis system that extracts and ranks relevant content from PDF collections based on specific personas and their job requirements.

## Features

- **Intelligent Section Detection**: Automatically identifies document structure and extracts meaningful sections
- **Persona-Aware Analysis**: Tailors content extraction based on user role and expertise level
- **Multi-Document Processing**: Handles collections of 3-10 related PDFs simultaneously
- **Relevance Ranking**: Uses TF-IDF and semantic similarity for accurate content prioritization
- **Sub-section Extraction**: Provides granular analysis of the most relevant content

## Architecture

```
Input PDFs + Persona + Job → Document Processing → Relevance Analysis → Ranked Output
```

### Core Components

1. **PDFContentExtractor**: Extracts structured content from PDF documents
2. **PersonaAnalyzer**: Generates domain-specific keywords from persona descriptions
3. **RelevanceScorer**: Ranks sections using TF-IDF and keyword matching
4. **OutputGenerator**: Creates structured JSON output in required format

## Technical Stack

- **Python 3.9**: Core runtime environment
- **pdfplumber**: PDF text extraction and structure analysis
- **NLTK**: Natural language processing toolkit
- **scikit-learn**: Machine learning algorithms for text analysis
- **numpy**: Numerical computations

## Installation & Usage

### Docker Deployment (Recommended)

```bash
# Build the Docker image
docker build --platform linux/amd64 -t persona-analyzer:latest .

# Run the container
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none \
  persona-analyzer:latest
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the analyzer
python persona_analyzer.py
```

## Input Format

### Directory Structure
```
/app/input/
├── document1.pdf
├── document2.pdf
├── document3.pdf
├── persona.txt        # Persona description
└── job.txt           # Job-to-be-done description
```

### Example Input Files

**persona.txt**:
```
PhD Researcher in Computational Biology with expertise in machine learning applications for drug discovery
```

**job.txt**:
```
Prepare a comprehensive literature review focusing on methodologies, datasets, and performance benchmarks
```

## Output Format

The system generates `analysis.json` with the following structure:

```json
{
  "metadata": {
    "input_documents": ["doc1.pdf", "doc2.pdf"],
    "persona": "PhD Researcher in Computational Biology",
    "job_to_be_done": "Prepare a comprehensive literature review",
    "processing_timestamp": "2025-07-26T10:30:00"
  },
  "extracted_sections": [
    {
      "document": "doc1.pdf",
      "page_number": 3,
      "section_title": "Methodology",
      "importance_rank": 1
    }
  ],
  "sub_section_analysis": [
    {
      "document": "doc1.pdf",
      "refined_text": "The proposed graph neural network approach...",
      "page_number": 3
    }
  ]
}
```

## Performance Characteristics

- **Processing Time**: ≤60 seconds for 3-5 documents
- **Model Size**: ≤1GB total footprint
- **CPU Only**: No GPU dependencies
- **Offline Operation**: No internet access required

## Algorithm Details

### Relevance Scoring
The system uses a multi-factor scoring approach:

1. **TF-IDF Similarity**: Semantic similarity between content and persona/job requirements
2. **Keyword Matching**: Direct matches with persona and job-specific terms
3. **Title Weighting**: Higher importance for section headings
4. **Combined Score**: `similarity_score + (persona_matches * 0.3 + job_matches * 0.4 + title_matches * 0.5) / 10`

### Section Detection
Uses pattern-based heading detection:
- Numbered sections (1., 1.1, 1.1.1)
- Chapter/Section markers
- All-caps headings
- Title case formatting

## Error Handling

- **Malformed PDFs**: Graceful degradation with error logging
- **Missing Text**: Fallback to simple keyword matching
- **Empty Documents**: Appropriate error messages and skipping
- **Memory Constraints**: Chunked processing for large document collections

## Development Notes

- Keep the Git repository private until competition deadline
- Ensure Docker compatibility with AMD64 architecture
- Test with diverse document types and personas
- Optimize for both accuracy and performance within constraints

## Support

For technical issues or questions about the implementation, refer to the approach_explanation.md document for detailed methodology information.
