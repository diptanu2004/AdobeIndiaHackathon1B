import json
import os
import re
import pdfplumber
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class PersonaDrivenAnalyzer:
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
    def process_documents(self, input_dir: str, persona: str, job_to_be_done: str, output_file: str):
        """
        Main processing function that analyzes documents based on persona and job requirements
        """
        # Read all PDFs from input directory
        pdf_files = [f for f in os.listdir(input_dir) if f.endswith('.pdf')]
        
        if not pdf_files:
            print("No PDF files found in input directory")
            return
        
        print(f"Processing {len(pdf_files)} documents for persona: {persona}")
        print(f"Job to be done: {job_to_be_done}")
        
        # Extract content and sections from all documents
        documents_data = []
        all_sections = []
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(input_dir, pdf_file)
            doc_data = self._extract_document_content(pdf_path)
            documents_data.append(doc_data)
            all_sections.extend(doc_data['sections'])
        
        # Analyze relevance based on persona and job
        persona_keywords = self._extract_persona_keywords(persona)
        job_keywords = self._extract_job_keywords(job_to_be_done)
        
        # Rank sections by relevance
        ranked_sections = self._rank_sections(all_sections, persona_keywords, job_keywords, job_to_be_done)
        
        # Extract sub-sections for top sections
        enhanced_sections = []
        for section in ranked_sections[:20]:  # Process top 20 sections
            sub_sections = self._extract_subsections(section, persona_keywords, job_keywords)
            enhanced_sections.append({
                **section,
                'sub_sections': sub_sections
            })
        
        # Generate output
        output = self._generate_output(
            documents_data, 
            enhanced_sections, 
            persona, 
            job_to_be_done
        )
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"Analysis complete. Results saved to {output_file}")
    
    def _extract_document_content(self, pdf_path: str) -> Dict:
        """
        Extract structured content from a PDF document
        """
        sections = []
        filename = os.path.basename(pdf_path)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                current_section = None
                current_text = []
                
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    lines = text.split('\n')
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Check if line is a heading
                        if self._is_heading(line):
                            # Save previous section
                            if current_section and current_text:
                                sections.append({
                                    'document': filename,
                                    'page': current_section['page'],
                                    'section_title': current_section['title'],
                                    'content': ' '.join(current_text),
                                    'importance_rank': 0  # Will be calculated later
                                })
                            
                            # Start new section
                            current_section = {
                                'title': self._clean_heading(line),
                                'page': page_num
                            }
                            current_text = []
                        else:
                            # Add to current section content
                            if current_section:
                                current_text.append(line)
                
                # Don't forget the last section
                if current_section and current_text:
                    sections.append({
                        'document': filename,
                        'page': current_section['page'],
                        'section_title': current_section['title'],
                        'content': ' '.join(current_text),
                        'importance_rank': 0
                    })
        
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")
        
        return {
            'filename': filename,
            'sections': sections
        }
    
    def _is_heading(self, line: str) -> bool:
        """
        Determine if a line is likely a heading
        """
        line = line.strip()
        
        # Pattern-based heading detection
        heading_patterns = [
            r'^\d+\.\s+[A-Z]',  # "1. Introduction"
            r'^\d+\.\d+\s+[A-Z]',  # "1.1 Overview"
            r'^[A-Z][A-Z\s]+$',  # "INTRODUCTION"
            r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)*$',  # "Introduction to Methods"
            r'^Chapter\s+\d+',  # "Chapter 1"
            r'^Section\s+\d+',  # "Section 1"
        ]
        
        return any(re.match(pattern, line) for pattern in heading_patterns)
    
    def _clean_heading(self, heading: str) -> str:
        """
        Clean heading text
        """
        # Remove numbering
        heading = re.sub(r'^\d+(\.\d+)*\s+', '', heading)
        heading = re.sub(r'^Chapter\s+\d+:?\s*', '', heading, flags=re.IGNORECASE)
        heading = re.sub(r'^Section\s+\d+:?\s*', '', heading, flags=re.IGNORECASE)
        
        return heading.strip()
    
    def _extract_persona_keywords(self, persona: str) -> List[str]:
        """
        Extract relevant keywords from persona description
        """
        # Role-based keyword mapping
        role_keywords = {
            'researcher': ['research', 'study', 'analysis', 'methodology', 'findings', 'data', 'results'],
            'student': ['learn', 'understand', 'concept', 'theory', 'example', 'explanation', 'basics'],
            'analyst': ['trend', 'performance', 'metric', 'comparison', 'evaluation', 'assessment'],
            'journalist': ['fact', 'news', 'report', 'event', 'timeline', 'source', 'evidence'],
            'entrepreneur': ['opportunity', 'market', 'strategy', 'business', 'revenue', 'growth'],
            'salesperson': ['customer', 'benefit', 'value', 'feature', 'advantage', 'solution']
        }
        
        keywords = []
        persona_lower = persona.lower()
        
        # Extract keywords based on role
        for role, role_keywords_list in role_keywords.items():
            if role in persona_lower:
                keywords.extend(role_keywords_list)
        
        # Add domain-specific keywords
        if 'biology' in persona_lower or 'computational biology' in persona_lower:
            keywords.extend(['protein', 'gene', 'molecular', 'biological', 'drug', 'compound'])
        elif 'chemistry' in persona_lower:
            keywords.extend(['reaction', 'mechanism', 'chemical', 'molecular', 'synthesis'])
        elif 'investment' in persona_lower or 'financial' in persona_lower:
            keywords.extend(['revenue', 'profit', 'financial', 'investment', 'market', 'growth'])
        
        # Extract keywords from persona text itself
        words = word_tokenize(persona.lower())
        keywords.extend([self.stemmer.stem(word) for word in words if word not in self.stop_words and len(word) > 3])
        
        return list(set(keywords))
    
    def _extract_job_keywords(self, job_description: str) -> List[str]:
        """
        Extract keywords from job-to-be-done description
        """
        # Extract key action words and concepts
        job_lower = job_description.lower()
        
        # Action-based keywords
        if 'literature review' in job_lower:
            return ['methodology', 'approach', 'result', 'finding', 'comparison', 'evaluation']
        elif 'financial' in job_lower or 'revenue' in job_lower:
            return ['revenue', 'profit', 'financial', 'growth', 'investment', 'performance']
        elif 'exam' in job_lower or 'study' in job_lower:
            return ['concept', 'mechanism', 'theory', 'principle', 'example', 'definition']
        
        # Extract keywords from job description
        words = word_tokenize(job_lower)
        keywords = [self.stemmer.stem(word) for word in words if word not in self.stop_words and len(word) > 3]
        
        return keywords
    
    def _rank_sections(self, sections: List[Dict], persona_keywords: List[str], 
                      job_keywords: List[str], job_description: str) -> List[Dict]:
        """
        Rank sections based on relevance to persona and job requirements
        """
        if not sections:
            return []
        
        # Prepare texts for TF-IDF
        section_texts = [f"{section['section_title']} {section['content']}" for section in sections]
        
        # Create TF-IDF matrix
        try:
            tfidf_matrix = self.vectorizer.fit_transform(section_texts)
        except:
            # Fallback to simple keyword matching if TF-IDF fails
            return self._rank_sections_simple(sections, persona_keywords, job_keywords)
        
        # Create query vector from persona and job keywords
        query_text = ' '.join(persona_keywords + job_keywords + [job_description])
        query_vector = self.vectorizer.transform([query_text])
        
        # Calculate similarity scores
        similarity_scores = cosine_similarity(query_vector, tfidf_matrix).flatten()
        
        # Add additional scoring based on keyword matches
        for i, section in enumerate(sections):
            text = f"{section['section_title']} {section['content']}".lower()
            
            # Keyword match bonus
            persona_matches = sum(1 for keyword in persona_keywords if keyword in text)
            job_matches = sum(1 for keyword in job_keywords if keyword in text)
            
            # Title match bonus (headings are important)
            title_matches = sum(1 for keyword in persona_keywords + job_keywords 
                              if keyword in section['section_title'].lower())
            
            # Combine scores
            keyword_score = (persona_matches * 0.3 + job_matches * 0.4 + title_matches * 0.5) / 10
            final_score = similarity_scores[i] + keyword_score
            
            sections[i]['relevance_score'] = final_score
        
        # Sort by relevance score
        ranked_sections = sorted(sections, key=lambda x: x['relevance_score'], reverse=True)
        
        # Assign importance ranks
        for i, section in enumerate(ranked_sections):
            section['importance_rank'] = i + 1
        
        return ranked_sections
    
    def _rank_sections_simple(self, sections: List[Dict], persona_keywords: List[str], 
                             job_keywords: List[str]) -> List[Dict]:
        """
        Simple keyword-based ranking fallback
        """
        for section in sections:
            text = f"{section['section_title']} {section['content']}".lower()
            
            persona_matches = sum(1 for keyword in persona_keywords if keyword in text)
            job_matches = sum(1 for keyword in job_keywords if keyword in text)
            title_matches = sum(1 for keyword in persona_keywords + job_keywords 
                              if keyword in section['section_title'].lower())
            
            section['relevance_score'] = persona_matches * 0.3 + job_matches * 0.4 + title_matches * 0.5
        
        ranked_sections = sorted(sections, key=lambda x: x['relevance_score'], reverse=True)
        
        for i, section in enumerate(ranked_sections):
            section['importance_rank'] = i + 1
        
        return ranked_sections
    
    def _extract_subsections(self, section: Dict, persona_keywords: List[str], 
                            job_keywords: List[str]) -> List[Dict]:
        """
        Extract and rank sub-sections from a main section
        """
        content = section['content']
        sentences = sent_tokenize(content)
        
        if len(sentences) < 3:
            return []
        
        # Group sentences into paragraphs/subsections
        subsections = []
        current_subsection = []
        
        for sentence in sentences:
            current_subsection.append(sentence)
            
            # Create subsection every 3-5 sentences or when we hit a logical break
            if len(current_subsection) >= 3:
                subsection_text = ' '.join(current_subsection)
                
                # Calculate relevance score
                text_lower = subsection_text.lower()
                persona_matches = sum(1 for keyword in persona_keywords if keyword in text_lower)
                job_matches = sum(1 for keyword in job_keywords if keyword in text_lower)
                relevance_score = persona_matches * 0.4 + job_matches * 0.6
                
                if relevance_score > 0:  # Only include relevant subsections
                    subsections.append({
                        'document': section['document'],
                        'refined_text': subsection_text,
                        'page_number': section['page'],
                        'relevance_score': relevance_score
                    })
                
                current_subsection = []
        
        # Handle remaining sentences
        if current_subsection:
            subsection_text = ' '.join(current_subsection)
            text_lower = subsection_text.lower()
            persona_matches = sum(1 for keyword in persona_keywords if keyword in text_lower)
            job_matches = sum(1 for keyword in job_keywords if keyword in text_lower)
            relevance_score = persona_matches * 0.4 + job_matches * 0.6
            
            if relevance_score > 0:
                subsections.append({
                    'document': section['document'],
                    'refined_text': subsection_text,
                    'page_number': section['page'],
                    'relevance_score': relevance_score
                })
        
        # Sort by relevance and return top 3
        return sorted(subsections, key=lambda x: x['relevance_score'], reverse=True)[:3]
    
    def _generate_output(self, documents_data: List[Dict], enhanced_sections: List[Dict], 
                        persona: str, job_to_be_done: str) -> Dict:
        """
        Generate the final output in required format
        """
        # Prepare document list
        input_documents = [doc['filename'] for doc in documents_data]
        
        # Prepare extracted sections
        extracted_sections = []
        sub_section_analysis = []
        
        for section in enhanced_sections[:15]:  # Top 15 sections
            extracted_sections.append({
                'document': section['document'],
                'page_number': section['page'],
                'section_title': section['section_title'],
                'importance_rank': section['importance_rank']
            })
            
            # Add sub-sections
            for sub_section in section.get('sub_sections', []):
                sub_section_analysis.append({
                    'document': sub_section['document'],
                    'refined_text': sub_section['refined_text'][:500] + "..." if len(sub_section['refined_text']) > 500 else sub_section['refined_text'],
                    'page_number': sub_section['page_number']
                })
        
        return {
            'metadata': {
                'input_documents': input_documents,
                'persona': persona,
                'job_to_be_done': job_to_be_done,
                'processing_timestamp': datetime.now().isoformat()
            },
            'extracted_sections': extracted_sections,
            'sub_section_analysis': sub_section_analysis
        }

def main():
    """
    Process documents from input directory and generate analysis
    """
    input_dir = "./input"
    output_file = "./output/analysis.json"
    
    # These would typically be read from input files or command line arguments
    # For the hackathon, you might read these from JSON files in the input directory
    persona_file = os.path.join(input_dir, "persona.txt")
    job_file = os.path.join(input_dir, "job.txt")
    
    try:
        with open(persona_file, 'r', encoding='utf-8') as f:
            persona = f.read().strip()
    except:
        persona = "PhD Researcher in Computational Biology"  # Default
    
    try:
        with open(job_file, 'r', encoding='utf-8') as f:
            job_to_be_done = f.read().strip()
    except:
        job_to_be_done = "Prepare a comprehensive literature review"  # Default
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Process documents
    analyzer = PersonaDrivenAnalyzer()
    analyzer.process_documents(input_dir, persona, job_to_be_done, output_file)

if __name__ == "__main__":
    main()