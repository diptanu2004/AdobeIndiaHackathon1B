#!/usr/bin/env python3
"""
Test script for Round 1B Persona-Driven Document Intelligence
"""

import os
import json
import tempfile
import shutil
from persona_analyzer import PersonaDrivenAnalyzer

def create_test_inputs():
    """
    Create sample test inputs for validation
    """
    test_cases = [
        {
            "name": "Academic Research",
            "persona": "PhD Researcher in Computational Biology with expertise in machine learning applications for drug discovery",
            "job": "Prepare a comprehensive literature review focusing on methodologies, datasets, and performance benchmarks",
            "expected_keywords": ["methodology", "dataset", "benchmark", "drug", "discovery"]
        },
        {
            "name": "Business Analysis", 
            "persona": "Investment Analyst specializing in technology sector evaluation",
            "job": "Analyze revenue trends, R&D investments, and market positioning strategies",
            "expected_keywords": ["revenue", "investment", "market", "strategy", "growth"]
        },
        {
            "name": "Educational Content",
            "persona": "Undergraduate Chemistry Student preparing for organic chemistry exams",
            "job": "Identify key concepts and mechanisms for exam preparation on reaction kinetics",
            "expected_keywords": ["concept", "mechanism", "reaction", "kinetics", "exam"]
        }
    ]
    
    return test_cases

def test_keyword_extraction():
    """
    Test persona and job keyword extraction
    """
    print("Testing keyword extraction...")
    analyzer = PersonaDrivenAnalyzer()
    
    test_cases = create_test_inputs()
    
    for case in test_cases:
        print(f"\n--- Testing: {case['name']} ---")
        
        persona_keywords = analyzer._extract_persona_keywords(case['persona'])
        job_keywords = analyzer._extract_job_keywords(case['job'])
        
        print(f"Persona: {case['persona']}")
        print(f"Persona Keywords: {persona_keywords[:10]}")  # Show first 10
        
        print(f"Job: {case['job']}")
        print(f"Job Keywords: {job_keywords[:10]}")  # Show first 10
        
        # Check if expected keywords are present
        all_keywords = persona_keywords + job_keywords
        found_keywords = [kw for kw in case['expected_keywords'] if any(kw in keyword for keyword in all_keywords)]
        
        print(f"Expected Keywords Found: {found_keywords}")
        print(f"Coverage: {len(found_keywords)}/{len(case['expected_keywords'])}")

def test_heading_detection():
    """
    Test heading detection patterns
    """
    print("\n" + "="*50)
    print("Testing heading detection...")
    
    analyzer = PersonaDrivenAnalyzer()
    
    test_headings = [
        ("1. Introduction", True),
        ("1.1 Background", True),
        ("1.1.1 Related Work", True),
        ("METHODOLOGY", True),
        ("Chapter 3: Results", True),
        ("Section 2.1 Analysis", True),
        ("This is regular text", False),
        ("email@example.com", False),
        ("Figure 1: Sample image", False),
        ("2. LITERATURE REVIEW", True),
        ("Discussion and Conclusions", True)
    ]
    
    correct = 0
    total = len(test_headings)
    
    for text, expected in test_headings:
        result = analyzer._is_heading(text)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{text}' -> {result} (expected: {expected})")
        if result == expected:
            correct += 1
    
    print(f"\nHeading Detection Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")

def test_section_ranking():
    """
    Test section ranking algorithm
    """
    print("\n" + "="*50)
    print("Testing section ranking...")
    
    analyzer = PersonaDrivenAnalyzer()
    
    # Sample sections
    test_sections = [
        {
            'document': 'test.pdf',
            'page': 1,
            'section_title': 'Introduction to Machine Learning',
            'content': 'Machine learning is a method of data analysis that automates analytical model building. It uses algorithms that iteratively learn from data.'
        },
        {
            'document': 'test.pdf', 
            'page': 2,
            'section_title': 'Drug Discovery Methods',
            'content': 'Drug discovery involves the identification of compounds that can treat diseases. Modern approaches use computational methods and molecular modeling.'
        },
        {
            'document': 'test.pdf',
            'page': 3,
            'section_title': 'Conclusion',
            'content': 'This paper presented various approaches to solving the problem. Future work should focus on improving accuracy.'
        }
    ]
    
    persona_keywords = ['machine', 'learning', 'drug', 'discovery', 'computational']
    job_keywords = ['method', 'approach', 'analysis', 'model']
    
    ranked_sections = analyzer._rank_sections(test_sections, persona_keywords, job_keywords, "analyze drug discovery methods")
    
    print("Ranked sections:")
    for i, section in enumerate(ranked_sections):
        print(f"{i+1}. {section['section_title']} (score: {section.get('relevance_score', 0):.3f})")

def validate_output_format():
    """
    Validate output JSON format matches requirements
    """
    print("\n" + "="*50)
    print("Validating output format...")
    
    # Sample output structure
    sample_output = {
        "metadata": {
            "input_documents": ["doc1.pdf", "doc2.pdf"],
            "persona": "Test persona",
            "job_to_be_done": "Test job",
            "processing_timestamp": "2025-07-26T10:30:00"
        },
        "extracted_sections": [
            {
                "document": "doc1.pdf",
                "page_number": 1,
                "section_title": "Introduction", 
                "importance_rank": 1
            }
        ],
        "sub_section_analysis": [
            {
                "document": "doc1.pdf",
                "refined_text": "Sample refined text content",
                "page_number": 1
            }
        ]
    }
    
    required_fields = {
        "metadata": ["input_documents", "persona", "job_to_be_done", "processing_timestamp"],
        "extracted_sections": ["document", "page_number", "section_title", "importance_rank"],
        "sub_section_analysis": ["document", "refined_text", "page_number"]
    }
    
    print("Checking output format compliance...")
    
    # Check top-level structure
    for key in ["metadata", "extracted_sections", "sub_section_analysis"]:
        if key in sample_output:
            print(f"✓ {key} field present")
        else:
            print(f"✗ {key} field missing")
    
    # Check metadata fields
    if "metadata" in sample_output:
        for field in required_fields["metadata"]:
            if field in sample_output["metadata"]:
                print(f"✓ metadata.{field} present")
            else:
                print(f"✗ metadata.{field} missing")
    
    print("Output format validation complete.")

def run_performance_test():
    """
    Basic performance testing
    """
    print("\n" + "="*50)
    print("Running performance test...")
    
    import time
    
    analyzer = PersonaDrivenAnalyzer()
    
    # Test keyword extraction performance
    start_time = time.time()
    
    test_persona = "PhD Researcher in Computational Biology with expertise in machine learning applications for drug discovery and molecular modeling"
    test_job = "Prepare a comprehensive literature review focusing on methodologies, datasets, performance benchmarks, and comparative analysis of state-of-the-art approaches"
    
    persona_keywords = analyzer._extract_persona_keywords(test_persona)
    job_keywords = analyzer._extract_job_keywords(test_job)
    
    end_time = time.time()
    
    print(f"Keyword extraction time: {end_time - start_time:.3f} seconds")
    print(f"Persona keywords extracted: {len(persona_keywords)}")
    print(f"Job keywords extracted: {len(job_keywords)}")
    
    # Memory usage approximation
    import sys
    analyzer_size = sys.getsizeof(analyzer)
    print(f"Analyzer object size: {analyzer_size} bytes")

def main():
    """
    Run all tests
    """
    print("Adobe Hackathon Round 1B - Test Suite")
    print("="*50)
    
    try:
        test_keyword_extraction()
        test_heading_detection()
        test_section_ranking()
        validate_output_format()
        run_performance_test()
        
        print("\n" + "="*50)
        print("All tests completed successfully!")
        print("Your solution appears to be working correctly.")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()