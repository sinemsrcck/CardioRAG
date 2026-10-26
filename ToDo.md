# CardioRAG V4 — Development TODO List

**Last Updated:** October 25, 2026  
**Status:** Active Development

## Project Overview

CardioRAG V4 is a biomedical Retrieval-Augmented Generation (RAG) system designed to answer cardiovascular research questions using scientific literature.

The system combines ChromaDB semantic retrieval, SQLite FTS5/BM25 keyword retrieval, MySQL metadata management, Reciprocal Rank Fusion (RRF), Cross-Encoder reranking, and evidence-aware Turkish answer generation.

**Dataset:** 7,761 cardiovascular research PDFs  
**Embedding Model:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

## 1. Data and Database Infrastructure

- [x] Create MySQL database and tables.
- [x] Implement PDF → text → chunk processing pipeline.
- [x] Configure MiniLM embeddings and ChromaDB V4.
- [x] Implement SQLite FTS5/BM25 infrastructure.
- [x] Synchronize the first 50 PDFs across MySQL, ChromaDB, and BM25.
- [x] Match PMID, PMCID, DOI, and article metadata for 7,761 PDFs.
- [x] Import 7,761 article and PDF records into MySQL.
- [x] Complete ChromaDB indexing of 7,761 PDFs.
- [x] Implement error handling, duplicate detection, and resumable indexing.
- [x] Complete full MySQL chunk synchronization and verify record counts.
- [ ] Build and verify the full BM25 index. **(In progress: 206,000 / 320,550 chunks at last check)**
- [ ] Verify chunk consistency across ChromaDB, MySQL, and BM25.

## 2. Retrieval — Scientific Article Search

- [x] Implement multilingual MiniLM semantic retrieval.
- [x] Implement BM25 keyword retrieval.
- [x] Implement Turkish-to-English query translation.
- [x] Combine retrieval results using Reciprocal Rank Fusion (RRF).
- [x] Implement Cross-Encoder reranking.
- [x] Implement source diversity filtering.
- [x] Implement relevance threshold and insufficient-evidence handling.
- [ ] Optimize retrieval parameters (`top_k`, RRF, relevance threshold).
- [ ] Evaluate medical abbreviations and Turkish/English queries.

## 3. Answer Generation and Scientific Reliability

- [x] Implement academic Turkish answer generation.
- [x] Generate numbered citations in answers.
- [x] Validate citation numbers.
- [x] Retrieve article titles, PMID, DOI, and PubMed links from MySQL.
- [x] Display cited sources separately.
- [x] Integrate initial LLM-based evidence validation.
- [ ] Validate each scientific claim against its cited evidence.
- [ ] Correct or remove unsupported claims.
- [ ] Implement stricter validation for numerical, statistical, and clinical claims.
- [ ] Modularize answer-generation prompts.
- [ ] Improve handling of uncited answers and insufficient evidence.

## 4. Evaluation and Experiments

- [x] Prepare the initial 20-question evaluation dataset (15 cardiology + 5 out-of-scope).
- [x] Implement automated RAG evaluation script.
- [x] Implement evaluation reporting script.
- [ ] Create reference article/evidence annotations for evaluation questions. **(Started: relevance judgments CSV created)**
- [ ] Compare BM25 vs. Semantic vs. Hybrid retrieval.
- [ ] Compare retrieval performance before and after reranking.
- [ ] Calculate Recall@5, MRR@10, and nDCG@10.
- [ ] Evaluate answer correctness, faithfulness, and citation accuracy.
- [ ] Evaluate rejection of out-of-domain questions.
- [ ] Run the 20-question evaluation on the full collection.
- [ ] Prepare error analysis and evaluation report.

### Evaluation Infrastructure Progress

- [x] Add optional retrieval debug output to `answer_hybrid_v4()`.
- [x] Preserve normal answer API compatibility.
- [x] Capture Semantic, BM25, RRF, and reranked chunk rankings.
- [x] Capture retrieved PMID, DOI, and filename information.
- [x] Implement unique article ranking helper.
- [x] Prepare article-level ranking fields in evaluation CSV.
- [x] Create `data/evaluation/relevance_judgments_v4.csv`.
- [ ] Generate candidate article pools for relevance assessment.
- [ ] Annotate candidate articles using relevance grades (0, 1, 2).
- [ ] Implement ranking metrics using independently assessed relevance labels.

## 5. User Interface and Delivery

- [x] Implement Streamlit question-answering interface.
- [x] Display article titles, PMID, DOI, and PubMed links.
- [x] Display PDF filenames and page information.
- [x] Implement question history and system information sections.
- [ ] Improve loading indicators, error handling, and user messages.
- [ ] Complete README, requirements, and installation instructions.
- [ ] Perform final end-to-end system testing.
- [ ] Finalize project documentation and GitHub delivery.

## 6. Optional Research — CardioRAG V5

- [ ] Experiment with sentence-aware chunking on a small PDF subset.
- [ ] Compare V4 and V5 chunking using the same reference questions.
- [ ] Create a separate V5 index if necessary, preserving V4.
- [ ] Expand V5 to the full collection only if meaningful improvements are demonstrated.

---

## Current Priorities

1. Finish BM25 indexing and verify all 320,550 chunks.
2. Validate consistency across ChromaDB, MySQL, and BM25.
3. Generate candidate article pools for the 15 cardiology evaluation questions.
4. Create independently assessed relevance judgments.
5. Run the 20-question evaluation on the complete collection.
6. Compare retrieval methods and calculate ranking metrics.
7. Strengthen claim-level citation and evidence validation.
8. Complete Streamlit testing and project documentation.

## Indexing Summary

| Metric | Result |
|---|---|
| Total PDFs indexed | 7,761 |
| ChromaDB chunks | 320,550 |
| MySQL chunks | 320,550 |
| Newly imported MySQL chunks | 318,572 |
| Previously existing MySQL chunks | 1,978 |
| Unmatched PDF identities | 0 |
| BM25 chunks at last check | 206,000 / 320,550 |
| Final ChromaDB indexing run failures | 0 |
| Final ChromaDB indexing run duration | 21,062.70 seconds |

**Note:** The V4 index should remain unchanged during retrieval and answer-generation improvements. Alternative chunking experiments should use a separate V5 collection.

---

*This roadmap will be updated as development and evaluation tasks are completed.*


python -m streamlit run app.py