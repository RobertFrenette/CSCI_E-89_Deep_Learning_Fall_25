#!/usr/bin/env python3
"""
Simple test script for RAG system evaluation.
Quick accuracy check for class project.

Usage:
    python test.py
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Ensure project root is in sys.path for sibling package imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from eval import RAGEvaluator, evaluate_test_case, calculate_aggregate_metrics

def load_test_data():
    """
    Load test cases from JSON file. Returns dictionary of test cases.
    """
    test_file = Path(__file__).parent / "test_data.json"
    with open(test_file, 'r') as f:
        return json.load(f)

def run_tests(test_cases):
    """
    Run evaluation tests. Executes all test cases and collects results.
    
    Params:
        test_cases (list): List of test case dictionaries.
    
    Returns:
        list: List of result dictionaries for each test case.
    
    Throws:
        Exception: If an error occurs during test case evaluation.
    """
    print(f"\n{'='*60}")
    print(f"Running {len(test_cases)} tests...")
    print(f"{'='*60}\n")
    
    evaluator = RAGEvaluator()
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] {test_case['id']}: {test_case['question']}")
        
        try:
            result = evaluate_test_case(evaluator, test_case)
            results.append(result)
            
            if result.get("success"):
                print(f"  ✓ Pass")
            else:
                print(f"  ✗ Fail")
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            results.append({
                "test_id": test_case.get("id", ""),
                "success": False,
                "error": str(e)
            })
    
    return results

def print_summary(results, elapsed_time=None):
    """
    Print test summary. Displays aggregate metrics including success rate, RAG metrics, and SQL metrics.
    
    Params:
        results (list): List of result dictionaries for each test case.
        elapsed_time (float, optional): Total elapsed time for running tests in seconds.
        
    Returns:
        None
    """
    aggregate = calculate_aggregate_metrics(results)
    
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    print(f"\nTotal Tests: {aggregate['total_tests']}")
    print(f"Passed: {aggregate['successful_tests']}")
    print(f"Failed: {aggregate['total_tests'] - aggregate['successful_tests']}")
    print(f"Success Rate: {aggregate['success_rate']:.1%}")
    
    if aggregate.get('rag_tests', 0) > 0:
        print(f"\nRAG Tests: {aggregate['rag_tests']}")
        print(f"  Avg Context Precision: {aggregate.get('rag_avg_context_precision', 0):.2f}")
        print(f"  Avg Answer Relevance: {aggregate.get('rag_avg_answer_relevance', 0):.2f}")
    
    if aggregate.get('sql_tests', 0) > 0:
        print(f"\nSQL Tests: {aggregate['sql_tests']}")
        print(f"  Success Rate: {aggregate.get('sql_success_rate', 0):.1%}")
        print(f"  Avg Result Count: {aggregate.get('sql_avg_result_count', 0):.1f}")
    
    if elapsed_time is not None:
        print(f"\nOverall Elapsed Time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
    
    print(f"\n{'='*60}\n")

def main():
    """
    Main function to run test suite. Loads test data, runs all tests, calculates metrics, and saves results to JSON file.
    """
    # Start timer
    start_time = time.time()
    
    # Load test data
    test_cases = load_test_data()['test_cases']
    
    # Run tests
    results = run_tests(test_cases)
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    # Print summary with elapsed time
    print_summary(results, elapsed_time)
    
    # Save results (simple JSON)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(__file__).parent / "results" / f"test_results_{timestamp}.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "elapsed_time_seconds": elapsed_time,
            "aggregate": calculate_aggregate_metrics(results),
            "results": results
        }, f, indent=2)
    
    print(f"Results saved to: {output_file.name}\n")

if __name__ == "__main__":
    main()
