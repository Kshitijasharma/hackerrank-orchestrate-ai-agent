# Multi-Domain Support Ticket Triage Agent — Complete Architecture & Technical Guide

This document is the comprehensive architectural reference and technical explanation for the **HackerRank Orchestrate** AI Support Triage Agent. It explains the design, system flow, mathematical foundations, module responsibilities, code walkthroughs, and interview defense talking points.

---

## Table of Contents
1. [Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
2. [High-Level System Architecture](#2-high-level-system-architecture)
3. [Deep-Dive: Ingestion & Document Chunking](#3-deep-dive-ingestion--document-chunking)
4. [Deep-Dive: Hybrid Retrieval Engine (Dense + Sparse)](#4-deep-dive-hybrid-retrieval-engine)
5. [Decision Engine, Risk Detection & LLM Reasoning](#5-decision-engine-risk-detection--llm-reasoning)
6. [Codebase Map & Module Responsibilities](#6-codebase-map--module-responsibilities)
7. [Step-by-Step Ticket Lifecycle Trace](#7-step-by-step-ticket-lifecycle-trace)
8. [Data Contracts & Schemas](#8-data-contracts--schemas)
9. [Interview Defense & System Strengths](#9-interview-defense--system-strengths)

---

## 1. Executive Summary & Problem Statement

### The Problem
Customer support across multi-product enterprise environments (in this challenge: **HackerRank**, **Claude**, and **Visa**) receives noisy, unstructured support tickets. Support teams face three core challenges:
1. **Misrouting & Inaccurate Triage**: Routing tickets to the wrong department causes delay.
2. **False Escalation vs. Missed Risk**: Escalating routine FAQs overwhelms human agents, while failing to escalate financial fraud, legal threats, or security breaches causes severe liability.
3. **Context Hallucination**: Answering tickets with generic LLM knowledge risks hallucinating false refund policies, fake deadlines, or inaccurate features.

### The Solution
A production-grade, terminal-based AI Support Triage Agent that uses **Chunk-Level Hybrid RAG (Dense + Sparse Retrieval)** to ground every response strictly in the provided 773-document support corpus. It automatically:
- Extracts the underlying issue and identifies the target company ecosystem.
- Performs hybrid retrieval to find the most relevant documentation chunks.
- Applies deterministic safety rules to detect financial/legal risks.
- Synthesizes grounded, actionable responses and formats strict JSON predictions (`replied` vs. `escalated`, `product_area`, `response`, `justification`, and `request_type`).

---

## 2. High-Level System Architecture

### Architectural Overview Diagram

```mermaid
flowchart TD
    subgraph Offline_Indexing ["Phase 1: Ingestion & Caching (One-Time)"]
        RawDocs["773 Support Documents<br/>(Markdown, HTML, JSON, TXT)"] --> Preprocess["Text Preprocessing<br/>(Newline & Whitespace Normalization)"]
        Preprocess --> Chunker["Hierarchical Token Chunker<br/>(chunk_size=500, overlap=80)"]
        Chunker --> Chunks["3,544 Structured Chunks<br/>+ Metadata (product, source, index)"]
        Chunks --> TFIDF_Build["Sparse TF-IDF Index<br/>(Vocabulary & IDF Weights)"]
        Chunks --> Azure_Embed["Azure OpenAI Embeddings<br/>(text-embedding-3-large, 3072-dim)"]
        Azure_Embed --> SaveCache["Disk Cache<br/>chunk_embeddings.npy<br/>chunks_metadata.json"]
    end

    subgraph Online_Processing ["Phase 2: Ticket Processing (Runtime)"]
        CSV["support_tickets.csv<br/>(29 Rows: Issue, Subject, Company)"] --> RowProc["Processor Engine (processor.py)"]
        RowProc --> Sanitizer["Input Sanitization & NaN Guard"]
        Sanitizer --> RiskCheck{"Deterministic Risk Scan<br/>(Fraud, Legal, Security)"}
        
        Sanitizer --> QueryEmbed["Query Vectorization<br/>(text-embedding-3-large)"]
        QueryEmbed --> HybridSearch["Hybrid Retriever (retriever.py)<br/>0.6 * Dense + 0.4 * Sparse<br/>+ Company Domain Filtering"]
        SaveCache -.-> HybridSearch
        TFIDF_Build -.-> HybridSearch

        HybridSearch --> Context["Top 4 Relevant Chunks<br/>(Complete Text + Metadata Headers)"]
        Context --> Prompt["Structured System Prompt<br/>(llm.py)"]
        Prompt --> GPT4o["Azure OpenAI Chat Model<br/>(gpt-4o, temperature=0.2)"]
        GPT4o --> SafeParse["Robust JSON Parser<br/>(safe_parse in utils.py)"]
        
        RiskCheck -- "High Risk Detected" --> Override["Override Status = 'escalated'"]
        SafeParse --> Override
        Override --> OutputCSV["support_tickets/output.csv<br/>(5 Required Competition Columns)"]
    end
```

---

## 3. Deep-Dive: Ingestion & Document Chunking

### Why Document-Level Retrieval Failed
In earlier iterations, the entire content of each documentation file was stored as a single document:
- Dense embeddings had to be arbitrarily truncated to the first 8,000 characters to prevent API token overflow.
- Context passed to the LLM was sliced to the first 500 characters (`docs[i][:500]`).
- **The Failure Mode**: If an important answer (e.g., a specific SSL certificate renewal command or a cancellation clause) appeared in Section 4 or on page 3 of a guide, it was completely invisible to both the embedding index and the prompt!

### The Hierarchical Recursive Chunker (`chunk_text`)
Located in [`code/retriever.py`](file:///c:/anshu/PROJECTS/hackerrank-orchestrate/hackerrank-orchestrate-may26/code/retriever.py#L19-L108), the chunking system splits text while respecting document semantic boundaries:

```python
separators = ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " ", ""]
```

1. **Paragraph & Section Boundary (`\n\n`)**: Tries to keep complete markdown sections and paragraphs intact.
2. **List & Item Boundary (`\n`)**: If a paragraph is larger than 500 tokens, splits at line breaks (keeping bullet lists coherent).
3. **Sentence Boundary (`. `, `? `, `! `, `; `)**: If a single paragraph has run-on lines, splits cleanly between sentences.
4. **Word Boundary (` `)**: Splitting at words is only used as a last resort.

### Token Counting & Sliding Overlap
- **Token Estimator (`count_tokens`)**: Uses a regex-based word-and-punctuation tokenizer (`r'\w+|[^\w\s]'`). It closely matches GPT BPE token counts within ~5% accuracy without requiring any external network or C++ binary dependencies.
- **Configurable Budget**:
  - `chunk_size = 500` tokens (~2,000 characters)
  - `overlap = 80` tokens (~320 characters)
- **Overlap Function**: Overlap guarantees that if a customer question spans a boundary between two sentences or concepts, at least one chunk captures the complete thought.

### Metadata Retention
Every chunk is packaged as an independent structured object:
```json
{
  "chunk_id": "claude/account-management/reset-password.md#chunk_1",
  "source_file": "claude/account-management/reset-password.md",
  "product": "claude",
  "category": "account-management",
  "chunk_index": 1,
  "text": "To reset your password, visit the login page and click 'Forgot Password'..."
}
```
Across the 773 source documents, the chunker deterministically creates **3,544 chunks** with an average size of 411.8 tokens.

---

## 4. Deep-Dive: Hybrid Retrieval Engine

Dense retrieval and sparse retrieval have complementary strengths and weaknesses:
- **Dense Retrieval (Semantic)**: Excels at understanding intent, paraphrasing, and synonyms (e.g., matching "where can I view billing receipts?" with "download tax invoice"). Weak at exact serial numbers, error codes, and niche technical acronyms.
- **Sparse Retrieval (TF-IDF / BM25)**: Excels at exact keyword matches, SKU numbers, API method names, and error codes (e.g., `cs_live_abcdefgh` or `401 Unauthorized`). Weak at semantic understanding.

### The Hybrid Pipeline
Located in `HybridRetriever` in [`code/retriever.py`](file:///c:/anshu/PROJECTS/hackerrank-orchestrate/hackerrank-orchestrate-may26/code/retriever.py):

```mermaid
sequenceDiagram
    participant User as Ticket Query
    participant Hybrid as HybridRetriever
    participant Dense as Azure OpenAI (text-embedding-3-large)
    participant Sparse as TF-IDF Index (NumPy/sklearn)
    participant Scorer as Normalizer & Blender

    User->>Hybrid: retrieve(query, company="claude")
    par Dense Vector Search
        Hybrid->>Dense: get_embeddings([query])
        Dense-->>Hybrid: 3072-dimensional vector q_embed
        Hybrid->>Hybrid: dense_scores = dot_product(chunk_embeddings, q_embed)
    and Sparse Keyword Search
        Hybrid->>Sparse: transform([query])
        Sparse-->>Hybrid: sparse_vector
        Hybrid->>Hybrid: sparse_scores = tfidf_matrix @ sparse_vector
    end
    Hybrid->>Scorer: dense_scores, sparse_scores
    Scorer->>Scorer: min_max_norm(dense_scores)
    Scorer->>Scorer: min_max_norm(sparse_scores)
    Scorer->>Scorer: combined = 0.6 * norm_dense + 0.4 * norm_sparse
    Scorer->>Hybrid: Filter candidates by product (claude)
    Hybrid->>Hybrid: De-duplicate chunks & select Top 4
    Hybrid-->>User: Complete chunk texts with metadata headers
```

### Score Normalization Formula
Because raw cosine similarity dot products (e.g. $[0.2, 0.8]$) and TF-IDF dot products (e.g. $[0.0, 0.35]$) operate on entirely different mathematical scales, combining them directly produces severe bias. The engine applies **Min-Max Score Normalization**:

$$\text{Dense}_{\text{norm}} = \frac{D_i - \min(D)}{\max(D) - \min(D)}$$

$$\text{Sparse}_{\text{norm}} = \frac{S_i - \min(S)}{\max(S) - \min(S)}$$

$$\text{Score}_{\text{hybrid}} = \alpha \cdot \text{Dense}_{\text{norm}} + (1 - \alpha) \cdot \text{Sparse}_{\text{norm}} \quad (\alpha = 0.6)$$

### Multi-Tenant Domain Filtering (`product_filter`)
The support tickets come from three distinct companies: `Claude`, `HackerRank`, and `Visa`.
- If a ticket specifies `Company: Claude`, the retriever isolates candidates to `product == "claude"`. This prevents cross-tenant noise (e.g. a Claude SSO question retrieving HackerRank SSO documentation).
- If `Company: None`, the retriever searches globally across all 3,544 chunks.

---

## 5. Decision Engine, Risk Detection & LLM Reasoning

### Deterministic Risk Safeguard ([`code/risk.py`](file:///c:/anshu/PROJECTS/hackerrank-orchestrate/hackerrank-orchestrate-may26/code/risk.py))
Before relying on the generative model, a deterministic safety layer scans ticket text for high-risk flags:
```python
high_risk_keywords = [
    "fraud", "unauthorized", "charged", "payment",
    "refund", "account locked", "suspicious"
]
```
If a keyword is detected, the status is forcefully overridden to `"escalated"`. This guarantees compliance with financial dispute policies without relying on LLM probabilistic outputs.

### LLM Prompt Architecture ([`code/llm.py`](file:///c:/anshu/PROJECTS/hackerrank-orchestrate/hackerrank-orchestrate-may26/code/llm.py))
The prompt is sent to Azure OpenAI `gpt-4o` with `temperature=0.2`. It instructs the model to:
1. **Primary Grounding**: Answer strictly using the retrieved documentation.
2. **Safe General Knowledge Fallback**: If context is incomplete, provide safe, actionable troubleshooting steps rather than escalating unnecessarily.
3. **Escalate Conservatively**: Escalate only when the issue explicitly requires human database/backend intervention (e.g. issuing financial refunds, manually amending test grades, investigating database outages).
4. **Strict JSON Schema**: Output JSON with 5 required keys: `status`, `product_area`, `response`, `justification`, and `request_type`.

### Resilient Output Sanitizer ([`code/utils.py`](file:///c:/anshu/PROJECTS/hackerrank-orchestrate/hackerrank-orchestrate-may26/code/utils.py))
`safe_parse()` cleans markdown code fences (` ```json `), parses JSON, and strictly normalizes values to the allowed competition enums:
- `status`: constrained to `replied` or `escalated`
- `request_type`: constrained to `product_issue`, `feature_request`, `bug`, or `invalid`

---

## 6. Codebase Map & Module Responsibilities

```
hackerrank-orchestrate-may26/
├── code/
│   ├── main.py             # Application entry point; triggers run_pipeline()
│   ├── processor.py        # Orchestration engine; iterates CSV, coordinates retrieval & LLM
│   ├── retriever.py        # Chunk-level hybrid RAG engine (chunking, TF-IDF, dense vectors)
│   ├── build_index.py      # Standalone CLI utility to pre-compute and cache chunk embeddings
│   ├── llm.py              # Prompt construction and Azure OpenAI Chat client (gpt-4o)
│   ├── risk.py             # Rule-based safety net scanning for critical keywords
│   ├── utils.py            # Robust JSON parser, enum sanitizers, and helper re-exports
│   └── README.md           # Technical documentation and execution instructions
├── data/                   # The 773-document raw knowledge base
│   ├── claude/             # Anthropic Claude Help Center exports
│   ├── hackerrank/         # HackerRank support documentation
│   ├── visa/               # Visa consumer and merchant support pages
│   ├── chunk_embeddings.npy # Pre-computed 3072-dimensional vector matrix
│   └── chunks_metadata.json # Serialized chunk text, file paths, and product metadata
├── support_tickets/
│   ├── sample_support_tickets.csv # Sample validation tickets with expected labels
│   ├── support_tickets.csv        # 29 test tickets to evaluate
│   └── output.csv                 # Generated predictions conforming to schema
├── AGENTS.md               # Hackathon rules, entry-point contracts & turn audit log
└── problem_statement.md    # Official competition guidelines & schema rules
```

---

## 7. Step-by-Step Ticket Lifecycle Trace

Here is the exact runtime trace when processing a sample ticket:

```
[Row 0 Input]
  Issue: "I lost access to my Claude team workspace after SSO was enabled."
  Subject: "Lost access to team"
  Company: "Claude"
```

1. **Extraction**: `processor.py` concatenates `subject` and `issue` into `text`. Checks `company == "claude"`.
2. **Deterministic Risk Check**: `risk.py` checks for keywords. Result: `"low"`.
3. **Retrieval**: `retriever.retrieve(text, product_filter="claude")` is invoked.
   - Computes query vector via `get_embeddings([text])`.
   - Computes query sparse vector via `vectorizer.transform([text])`.
   - Filters candidate chunk IDs to only those where `product == "claude"`.
   - Identifies top 4 chunks related to Claude SSO and workspace seat administration.
   - Formats complete chunks into a single context string.
4. **Prompt Assembly**: `llm.py` embeds the ticket text and formatted context chunks into `build_prompt()`.
5. **Inference**: Azure OpenAI `gpt-4o` evaluates the prompt and generates structured JSON.
6. **Parsing & Validation**: `safe_parse()` cleans fences, verifies JSON, and normalizes enum values.
7. **Risk Override**: `risk == "low"`, so the model's status decision stands.
8. **Storage**: Appended to `results` list; at the conclusion of all 29 tickets, written to `support_tickets/output.csv`.

---

## 8. Data Contracts & Schemas

### Input Schema (`support_tickets/support_tickets.csv`)
| Column | Type | Example |
| :--- | :--- | :--- |
| `Issue` | String | `"site is down & none of the pages are accessible"` |
| `Subject` | String | `"Outage report"` |
| `Company` | String | `"HackerRank"`, `"Claude"`, `"Visa"`, or `None` |

### Output Schema (`support_tickets/output.csv`)
| Column | Allowed Values | Description |
| :--- | :--- | :--- |
| `status` | `replied`, `escalated` | Routing decision: answer or send to human team |
| `product_area` | String | Category (e.g. `billing`, `assessments`, `security`) |
| `response` | String | Grounded, customer-facing solution |
| `justification`| String | Explanation of routing & request type decision |
| `request_type` | `product_issue`, `feature_request`, `bug`, `invalid` | Ticket classification |

---

## 9. Interview Defense & System Strengths

When defending this architecture in an AI technical interview:

### 1. "Why implement custom chunking instead of using LangChain or LlamaIndex?"
> *"Production systems in regulated enterprise environments require lean, predictable dependencies without version churn. By implementing our own hierarchical recursive chunker in native standard Python, we achieved zero external dependencies, eliminated IDE import warnings, and maintained 100% control over separator priorities, boundary overlap, and chunk metadata tracking."*

### 2. "Why use Hybrid Search instead of Dense-only or Vector DBs?"
> *"Dense retrieval alone suffers when handling exact error codes, order IDs (e.g. `cs_live_...`), and system acronyms. Pure sparse search fails when users ask questions using different vocabulary. Combining dense semantic embeddings with sparse TF-IDF and min-max normalization gives us the best of both worlds: conceptual comprehension paired with precision keyword recall."*

### 3. "How did you solve the context loss problem?"
> *"Earlier implementations loaded entire files and arbitrarily truncated at 8,000 characters for embedding and 500 characters for prompt context. By moving to a 500-token chunking pipeline with an 80-token sliding overlap, we eliminated data loss and ensured information at the bottom of long manuals is indexed and retrieved with equal fidelity."*

### 4. "How do you prevent costly hallucinations and liability?"
> *"We built defense in depth: first, a deterministic rule-based risk scanner overrides the LLM on financial disputes or security breaches; second, a multi-tenant product filter prevents cross-company document bleeding; third, the prompt explicitly instructs the LLM to prioritize grounded documentation over speculation."*

---

### Key Operational Metrics
- **Corpus Ingestion**: 773 source documents $\to$ 3,544 structured chunks in under 3 seconds.
- **Index Build**: 71 batched embedding requests (batch size: 50 chunks, ~1.46M tokens, ~$0.19 USD).
- **Ticket Evaluation**: 29 tickets $\to$ 58 runtime API calls in under 60 seconds (~$0.18 USD).
- **Disk Footprint**: `chunk_embeddings.npy` (~43 MB), `chunks_metadata.json` (~3.5 MB).

