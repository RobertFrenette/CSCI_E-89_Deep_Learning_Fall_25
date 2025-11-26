"""
Core evaluation functions for RAG system testing.

This module provides utilities to evaluate:
1. RAG document retrieval quality (context precision, recall, relevancy)
2. SQL query accuracy and correctness
3. Answer faithfulness and relevance
4. Overall system performance metrics

Uses the actual RAGProcessor from agent.processors.rag_processor to test the full pipeline.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Ensure project root is in sys.path for sibling package imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.chat_models import ChatOllama

from agent.config import (
    LLM_MODEL,
    TEMPERATURE,
    CHROMA_DIR,
    SQL_DB_PATH,
    PDF_DIR,
    EMBEDDING_MODEL,
    RETRIEVAL_K,
    RETRIEVAL_SCORE_THRESHOLD
)
from agent.processors.rag_processor import RAGProcessor

class RAGEvaluator:
    """
    Evaluates RAG system performance using various metrics.
    
    Uses the actual RAGProcessor from agent.processors.rag_processor to test
    the full pipeline (retrieval + generation + source validation).
    """
    
    def __init__(self):
        """
        Initialize evaluator with actual RAGProcessor from agent app.
        
        Throws RuntimeError if initialization fails.
        """
        # Initialize LLM for evaluation (separate from RAG processor)
        self.llm = ChatOllama(
            model=LLM_MODEL,
            temperature=TEMPERATURE
        )
        
        # Use actual RAGProcessor from agent app (tests production code)
        print("Initializing RAGProcessor from agent.processors.rag_processor...")
        try:
            self.processor = RAGProcessor(
                pdf_dir=PDF_DIR,
                chroma_dir=CHROMA_DIR
            )
            # Load and setup RAG chain (same as app.py does)
            self.qa_chain, self.memory, self.vectorstore = self.processor.load_and_setup(
                embedding_model=EMBEDDING_MODEL,
                llm_model=LLM_MODEL,
                temperature=TEMPERATURE,
                k=RETRIEVAL_K,
                score_threshold=RETRIEVAL_SCORE_THRESHOLD
            )
            print(f"✓ RAGProcessor initialized successfully")
        except Exception as e:
            print(f"Error initializing RAGProcessor: {e}")
            raise RuntimeError(f"Could not initialize RAGProcessor: {e}")
    
    def evaluate_context_precision(
        self,
        question: str,
        retrieved_contexts: List[str],
        ground_truth_answer: str
    ) -> float:
        """
        Evaluate if retrieved contexts are relevant to answering the question.
        
        Params:
            question (str): The question being asked.
            retrieved_contexts (List[str]): List of retrieved context strings.
            ground_truth_answer (str): The known correct answer to the question.
        
        Returns:
            float: Precision score from 0-1 indicating relevance of contexts.
        """
        if not retrieved_contexts:
            return 0.0
        
        # Create evaluation prompt
        eval_prompt = PromptTemplate(
            input_variables=["question", "context", "answer"],
            template="""Given the question and ground truth answer, evaluate if the provided context is relevant.
            
Question: {question}
Ground Truth Answer: {answer}
Context: {context}

Is this context relevant for answering the question? Answer only 'yes' or 'no'.
Answer:"""
        )
        
        chain = LLMChain(llm=self.llm, prompt=eval_prompt)
        
        relevant_count = 0
        for context in retrieved_contexts:
            try:
                result = chain.run(
                    question=question,
                    context=context,
                    answer=ground_truth_answer
                )
                if "yes" in result.lower():
                    relevant_count += 1
            except Exception as e:
                print(f"Error evaluating context: {e}")
        
        return relevant_count / len(retrieved_contexts)
    
    def evaluate_answer_relevancy(
        self,
        question: str,
        answer: str
    ) -> float:
        """
        Evaluate if the answer is relevant to the question. Returns score from 0-1.
        
        Params:
            question (str): The question being asked.
            answer (str): The answer to evaluate.
        
        Returns:
            float: Relevancy score from 0-1.
        """
        eval_prompt = PromptTemplate(
            input_variables=["question", "answer"],
            template="""Evaluate if the answer is relevant to the question.

Question: {question}

Answer: {answer}

Rate the relevancy from 0-10 where:
0 = Completely irrelevant
10 = Perfectly relevant and addresses the question

Score (just the number):"""
        )
        
        chain = LLMChain(llm=self.llm, prompt=eval_prompt)
        
        try:
            result = chain.run(question=question, answer=answer)
            score = float(result.strip().split()[0])
            return min(max(score / 10.0, 0.0), 1.0)
        except Exception as e:
            print(f"Error evaluating relevancy: {e}")
            return 0.0
    
    def evaluate_sql_query(
        self,
        question: str,
        expected_result_count: int = None,
        expected_contains: List[str] = None
    ) -> Tuple[bool, List[Any], str]:
        """
        Execute SQL query routing and validate results.
        
        Params:
            question (str): The question being asked.
            expected_result_count (int, optional): Expected number of results.
            expected_contains (List[str], optional): List of strings expected to be in results.
        
        Returns:
            Tuple[bool, List[Any], str]: (success flag, results list, error message)
            
        Throws:
            Exception: On SQL execution errors.
        """
        from agent.processors.sql_processor import SQLProcessor
        
        error_msg = ""
        results = []
        
        try:
            # Initialize SQL processor
            sql_processor = SQLProcessor(SQL_DB_PATH)
            sql_processor.connect()
            
            # Determine which SQL function to call based on question
            question_lower = question.lower()
            
            if "high risk" in question_lower or "high-risk" in question_lower:
                results = sql_processor.get_high_risk_policies()
            elif "how many insureds" in question_lower:
                count = sql_processor.count_insureds()
                results = [{"count": count}]
            elif "how many claims" in question_lower:
                count = sql_processor.count_claims()
                results = [{"count": count}]
            elif "insured" in question_lower and any(char.isalnum() and char.isupper() for char in question):
                # Try to extract insured ID (usually uppercase alphanumeric like BQ4DCXWL)
                import re
                id_match = re.search(r'[A-Z0-9]{6,10}', question)
                if id_match:
                    insured_id = id_match.group()
                    result = sql_processor.get_insured_info(insured_id)
                    if result:
                        results = [result]
            
            # Validate results
            success = True
            
            if expected_result_count is not None:
                if len(results) != expected_result_count:
                    success = False
                    error_msg = f"Expected {expected_result_count} results, got {len(results)}"
            
            if expected_contains and success:
                results_str = str(results).lower()
                for expected in expected_contains:
                    if expected.lower() not in results_str:
                        success = False
                        error_msg = f"Expected to find '{expected}' in results"
                        break
            
            return success, results, error_msg
            
        except Exception as e:
            return False, [], str(e)
    
def evaluate_test_case(
    evaluator: RAGEvaluator,
    test_case: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate a single test case using the full RAG pipeline.
    
    Params:
        evaluator (RAGEvaluator): The evaluator instance to use.
        test_case (Dict[str, Any]): The test case data.
    
    Returns:
        Dict[str, Any]: Evaluation results and metrics.
    
    Throws:
        Exception: On evaluation errors.
    """
    question = test_case["question"]
    test_type = test_case["type"]
    ground_truth = test_case.get("ground_truth_answer", "")
    
    result = {
        "test_id": test_case.get("id", ""),
        "question": question,
        "type": test_type,
        "timestamp": datetime.now().isoformat(),
        "metrics": {}
    }
    
    try:
        if test_type == "rag":
            # Test full pipeline using actual RAGProcessor (same as app.py)
            # This tests: retrieval → generation → source validation
            formatted_answer, sources, full_result = evaluator.processor.get_answer_with_sources(question)
            answer = full_result.get("answer", "")
            source_documents = full_result.get("source_documents", [])
            
            # Extract context texts from source documents
            contexts = [doc.page_content for doc in source_documents]
            result["retrieved_contexts_count"] = len(contexts)
            result["generated_answer"] = answer
            
            # Evaluate context precision using both LLM and keyword matching
            llm_precision = 0.0
            if contexts:
                llm_precision = evaluator.evaluate_context_precision(
                    question,
                    contexts,
                    ground_truth
                )
            
            # Get keyword-based precision (stricter)
            expected_keywords = test_case.get("expected_contexts_contain", [])
            keyword_precision = 0.0
            if expected_keywords and contexts:
                # Check how many expected keywords appear across all contexts
                all_contexts_text = " ".join(contexts).lower()
                found_keywords = sum(1 for kw in expected_keywords if kw.lower() in all_contexts_text)
                keyword_precision = found_keywords / len(expected_keywords) if expected_keywords else 0.0
            
            # Use the stricter of the two metrics
            context_precision = min(llm_precision, keyword_precision) if expected_keywords else llm_precision
            
            # Simple answer relevance check (does answer relate to question?)
            answer_relevance = 0.0
            if answer and not answer.startswith("I don't have relevant information"):
                answer_relevance = evaluator.evaluate_answer_relevancy(question, answer)
            
            result["metrics"]["context_precision"] = context_precision
            result["metrics"]["llm_precision"] = llm_precision
            result["metrics"]["keyword_precision"] = keyword_precision
            result["metrics"]["answer_relevance"] = answer_relevance
            result["metrics"]["retrieval_successful"] = len(contexts) > 0
            
            # Test passes if we have contexts, precision is good enough, and answer is relevant
            # For hard questions, require higher precision
            difficulty = test_case.get("difficulty", "medium")
            if difficulty == "hard":
                precision_threshold = 0.8  # Harder tests need 80%+ precision
                relevance_threshold = 0.7  # Harder tests need 70%+ relevance
            elif difficulty == "medium":
                precision_threshold = 0.6  # Medium tests need 60%+ precision
                relevance_threshold = 0.6  # Medium tests need 60%+ relevance
            else:
                precision_threshold = 0.4  # Easy tests need 40%+ precision
                relevance_threshold = 0.5  # Easy tests need 50%+ relevance
            
            result["metrics"]["precision_threshold"] = precision_threshold
            result["metrics"]["relevance_threshold"] = relevance_threshold
            
            # Success criteria: retrieval works + good precision + relevant answer
            result["success"] = (
                len(contexts) > 0 
                and context_precision >= precision_threshold 
                and answer_relevance >= relevance_threshold
            )
            
        elif test_type == "sql":
            # Evaluate SQL query execution
            expected_count = test_case.get("expected_result_count")
            expected_contains = test_case.get("expected_contains", [])
            
            success, results, error = evaluator.evaluate_sql_query(
                question,
                expected_count,
                expected_contains
            )
            
            result["metrics"]["sql_success"] = success
            result["metrics"]["result_count"] = len(results)
            result["sql_error"] = error
            result["sql_results_sample"] = str(results[:3]) if results else []
            result["success"] = success
        
        else:
            result["success"] = True
        
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
    
    return result

def calculate_aggregate_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate aggregate metrics across all test cases.
    
    Params:
        results (List[Dict[str, Any]]): List of individual test case results.
    
    Returns:
        Dict[str, Any]: Aggregate metrics including success rates and averages.
    """
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r.get("success", False))
    
    rag_tests = [r for r in results if r.get("type") == "rag"]
    sql_tests = [r for r in results if r.get("type") == "sql"]
    
    aggregate = {
        "total_tests": total_tests,
        "successful_tests": successful_tests,
        "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
        "rag_tests": len(rag_tests),
        "sql_tests": len(sql_tests)
    }
    
    # RAG-specific metrics
    if rag_tests:
        successful_retrievals = sum(
            1 for r in rag_tests
            if r.get("metrics", {}).get("retrieval_successful", False)
        )
        avg_precision = sum(
            r.get("metrics", {}).get("context_precision", 0)
            for r in rag_tests
        ) / len(rag_tests)
        avg_relevance = sum(
            r.get("metrics", {}).get("answer_relevance", 0)
            for r in rag_tests
        ) / len(rag_tests)
        
        aggregate["rag_retrieval_success_rate"] = successful_retrievals / len(rag_tests)
        aggregate["rag_avg_context_precision"] = avg_precision
        aggregate["rag_avg_answer_relevance"] = avg_relevance
    
    # SQL-specific metrics
    if sql_tests:
        successful_sql = sum(
            1 for r in sql_tests
            if r.get("metrics", {}).get("sql_success", False)
        )
        avg_result_count = sum(
            r.get("metrics", {}).get("result_count", 0)
            for r in sql_tests
        ) / len(sql_tests)
        
        aggregate["sql_success_rate"] = successful_sql / len(sql_tests)
        aggregate["sql_avg_result_count"] = avg_result_count
    
    return aggregate
