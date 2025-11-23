# AI Agent Insure - Agent Assist Chatbot

**RAG & SQL Testing (For Class Project)**

Quick and basic accuracy testing for both RAG and SQL query systems.

## Overview

This is a simple test framework to validate that both the RAG system and SQL query routing work correctly. It runs test questions covering both RAG document retrieval and SQL database queries, showing pass/fail results with detailed metrics for each test type.

## Directory Structure

```
agent-eval/
├── eval.py              # Core evaluation functions
├── test_data.json       # Test questions (RAG and SQL)
├── test.py              # Main test script
├── analysis.ipynb       # Jupyter notebook for visualization
├── requirements.txt     # Python dependencies
├── README.md            # This file
└── results/             # Generated test results
```

## Quick Start

### 1. Install Dependencies

From the `agent-eval` directory:

```bash
uv pip install -r requirements.txt
```

This installs:

- LangChain and RAG framework dependencies
- ChromaDB vector database
- pandas, matplotlib (for charts)
- jupyter (for notebooks)

### 2. Run Tests

```bash
python test.py
```

### 3. View Results (Optional)

```bash
jupyter notebook analysis.ipynb
```

The notebook shows:

- Pass/fail summary
- Simple pie and bar charts
- List of any failed tests

**Note:** By default, the notebook loads the most recent results. To load a specific results file, edit the `RESULTS_FILE` constant in the second cell:

- `RESULTS_FILE = None` (default - loads latest)
- `RESULTS_FILE = "test_results_20251118_143022.json"` (loads specific file)

## What This Does

### RAG Testing
- Tests your RAG system against questions (including multi-hop reasoning)
- Uses the actual `RAGProcessor` from `agent.processors.rag_processor` to test the full pipeline
- Tests complete flow: retrieval → answer generation → source validation
- Validates document retrieval quality and answer relevance
- Calculates context precision and answer relevance metrics
- Useful for demonstrating retrieval optimization (RETRIEVAL_K parameter)

### SQL Testing
- Tests SQL query routing and execution
- Validates SQL queries against the insured database
- Checks result accuracy and expected data presence
- Calculates SQL success rate and average result counts

### Overall
- Shows you what passed and what failed for both test types
- Displays separate metrics for RAG and SQL tests
- Tracks overall elapsed testing time

## Sample Output

```
============================================================
Running 10 tests...
============================================================

[1/10] rag_001: What is AI Agent Insure?
  ✓ Pass
[2/10] rag_002: What does Agentic AI Liability Insurance cover?
  ✓ Pass
...
[7/10] sql_001: How many insureds are there?
  ✓ Pass
[8/10] sql_002: How many claims are there?
  ✓ Pass
...

============================================================
TEST SUMMARY
============================================================

Total Tests: 10
Passed: 10
Failed: 0
Success Rate: 100.0%

RAG Tests: 6
  Avg Context Precision: 0.94
  Avg Answer Relevance: 0.75

SQL Tests: 4
  Success Rate: 100.0%
  Avg Result Count: 1.0

Overall Elapsed Time: 184.98 seconds (3.08 minutes)

============================================================

Results saved to: test_results_20251118_143022.json
```

## Test Data

The `test_data.json` file contains **test cases for both RAG and SQL**:

### RAG Tests (6 test cases)
- **Easy**: Basic company info, product descriptions
- **Medium**: Product details, coverage specifics, compliance information
- **Hard**: Multi-hop reasoning, complex product comparisons

### SQL Tests (4 test cases)
- **Easy**: Count queries (insureds, claims)
- **Medium**: Filter queries (high-risk policies)
- **Hard**: Lookup queries (specific insured information)

### Test Case Structure

**RAG tests include:**
- Question
- Expected answer (ground truth)
- Expected keywords/contexts to appear in retrieved documents
- Test category
- Difficulty level

**SQL tests include:**
- Question
- Expected result count
- Expected values to contain in results
- Test category
- Difficulty level

## Files Generated

Results are saved to `results/test_results_TIMESTAMP.json` with:

- Timestamp
- Pass/fail for each test
- Aggregate metrics
- Error messages for failures

## For Class Submission

1. Run `python test.py`
2. Screenshot the terminal output
3. Open `jupyter notebook analysis.ipynb`
4. Run all cells (Cell → Run All)
5. Screenshot the visualizations and metrics
6. Include both screenshots in your report

Shows that you validated your RAG system with actual testing. ✓

## Troubleshooting

### Import Errors

Make sure you're in the evaluation directory:

```bash
cd agent-eval
```

### No Results Found

Run the test script first:

```bash
python test.py
```

### ChromaDB Not Found

The evaluation uses your existing vector database from `../vector-store/chroma_db/` and the actual `RAGProcessor` from the agent app. Make sure you've:
1. Created the vector store: `python ../vector-store/create_chroma_vectorstore.py`
2. Created the SQL database: `python ../insured-db/create_and_seed_insureds_db.py`

### Demonstrating Improvement

1. Run tests with `RETRIEVAL_K = 2` in `../agent/config.py`
2. Note the context precision score (e.g., 0.68)
3. Change to `RETRIEVAL_K = 5` and run again
4. Compare metrics in notebook - should see 15-25% improvement

---

#### Credit: This markdown file was generated by 🤖 GitHub Copilot.
