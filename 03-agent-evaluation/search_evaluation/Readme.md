# RAG Search Algorithm Evaluation Process

This document outlines a systematic approach to evaluate different search methods or algorithms in RAG systems to determine which works best for your datasets.

## Overview

The evaluation process involves creating synthetic questions from your dataset, building a ground truth mapping, testing retrieval performance, and computing metrics to compare different search algorithms.

## Step-by-Step Process

### Step 1: Generate Synthetic Questions

For each record in your FAQ dataset:

- Generate 5 questions that can be answered by that document
- This creates a diverse set of queries for testing

```pseudocode
For each record in FAQ:
    generate 5 questions
```

### Step 2: Create Ground Truth Dataset

For each generated question, create a ground truth mapping:

- Map each question to its original source document
- Include the course/document ID for reference

**Ground Truth Format:**

```
[question, course_documentId_referencing_original_document]
```

```pseudocode
for each of the generated questions:
    create ground truth dataset by mapping each question to:
        - original document it comes from
        - course documentId
```

### Step 3: Evaluate Retrieval Performance

For each question in the ground truth dataset:

1. Execute a query using the question
2. Retrieve top-k documents (typically k=5)
3. Check if any returned documents match the expected documentId
4. Record the position of relevant documents

```pseudocode
for each question row in ground truth dataset [question, course_documentId]:
    query_results = make_query(question)  # returns top-k documents
    check if returned documents match expected documentId
    record position of matches
```

### Step 4: Generate Relevance Matrix

Create a boolean matrix showing relevant (True) vs non-relevant (False) documents at each position:

```python
example_results = [
    [True, False, False, False, False],   # Hit at position 1
    [False, False, False, False, False],  # No hits
    [False, False, False, False, False],  # No hits
    [False, False, False, False, False],  # No hits
    [False, False, False, False, False],  # No hits
    [True, False, False, False, False],   # Hit at position 1
    [True, False, False, False, False],   # Hit at position 1
    [True, False, False, False, False],   # Hit at position 1
    [True, False, False, False, False],   # Hit at position 1
    [True, False, False, False, False],   # Hit at position 1
    [False, False, True, False, False],   # Hit at position 3
    [False, False, False, False, False],  # No hits
]
```

## Metrics Calculation

### Hit Rate@k

Hit Rate measures the percentage of queries where at least one relevant document appears in the top-k results:

$$\text{Hit Rate@k} = \frac{\text{Number of queries with} \geq 1 \text{ relevant doc in top-k}}{\text{Total number of queries}}$$

**Example Calculation:**

- Total queries: 12
- Queries with hits: 7 (queries 1, 6, 7, 8, 9, 10, 11)
- Hit Rate@5 = 7/12 = 0.583 or 58.3%

### Mean Reciprocal Rank (MRR)

MRR measures the average reciprocal rank of the first relevant document:

$$\text{MRR} = \frac{1}{N} \times \sum_{i=1}^{N} \frac{1}{\text{rank}_i}$$

Where $\text{rank}_i$ is the position of the first relevant document for query $i$ (0 if no relevant document found).

**Example Calculation:**

- Query 1: rank = 1 → 1/1 = 1.0
- Query 2: rank = ∞ → 1/∞ = 0.0
- Query 3: rank = ∞ → 1/∞ = 0.0
- Query 4: rank = ∞ → 1/∞ = 0.0
- Query 5: rank = ∞ → 1/∞ = 0.0
- Query 6: rank = 1 → 1/1 = 1.0
- Query 7: rank = 1 → 1/1 = 1.0
- Query 8: rank = 1 → 1/1 = 1.0
- Query 9: rank = 1 → 1/1 = 1.0
- Query 10: rank = 1 → 1/1 = 1.0
- Query 11: rank = 3 → 1/3 = 0.333
- Query 12: rank = ∞ → 1/∞ = 0.0

$$\text{MRR} = \frac{1}{12} \times (1.0 + 0 + 0 + 0 + 0 + 1.0 + 1.0 + 1.0 + 1.0 + 1.0 + 0.333 + 0) = 0.528$$

## Interpretation

- **Higher Hit Rate**: Better at finding relevant documents somewhere in top-k results
- **Higher MRR**: Better at ranking relevant documents higher in the results
- **Perfect scores**: Hit Rate = 1.0, MRR = 1.0 (all queries return relevant doc at position 1)

## Usage

1. Run this evaluation process for each search algorithm you want to compare
2. Calculate Hit Rate and MRR for each algorithm
3. Choose the algorithm with the highest metric values
4. Consider both metrics together - high hit rate with low MRR might indicate good recall but poor ranking

The higher the metric values, the better the search method or algorithm being used for your specific dataset and use case.
