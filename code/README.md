# AI Support Triage Agent - /code

This directory contains the core logic for the Support Ticket Triage AI Agent. It implements a highly optimized **Hybrid RAG (Retrieval-Augmented Generation)** pipeline using Azure OpenAI to process, analyze, and resolve customer support tickets intelligently.

<img width="692" height="308" alt="1" src="https://github.com/user-attachments/assets/8493322b-f8ab-4042-823c-fda08a2fbd7c" />

<img width="616" height="418" alt="2" src="https://github.com/user-attachments/assets/e11b1061-e442-4abf-8e6d-85dfc56cb78d" />



## 🏗️ Architecture & Modules: 

The pipeline is designed to be modular, separating data orchestration, retrieval, LLM interaction, and risk assessment into distinct files.

### Core Execution
* **`main.py`**  
  The primary entry point for the application. It initializes the environment, authenticates with Azure OpenAI, and triggers the ticket processing loop.
* **`processor.py`**  
  The orchestration engine. It reads the raw `support_tickets.csv`, sanitizes the inputs (handling NaNs and empty rows), coordinates the flow between the retriever and the LLM, and formats the final `output.csv`.

### Intelligence & RAG:

* **`retriever.py`**  
  The intelligence backbone implementing the Hybrid RAG system. It combines `scikit-learn`'s TF-IDF for exact-keyword (sparse) retrieval with Azure OpenAI's `text-embedding-3-large` for semantic (dense) retrieval. It features intelligent chunking, 8,000-character truncation to prevent token overflow, and automatic caching logic.
  
* **`build_index.py`**  
  A standalone utility script to generate and locally cache the document embeddings (`embeddings.npy`). Running this script once saves thousands of API tokens and drastically speeds up execution times.
  
* **`llm.py`**  
  Manages communication with the Azure OpenAI Chat model (`gpt-4o`). Contains the heavily engineered system prompt that forces the agent to extract structured JSON, securely reason through sparse context, and aggressively minimize unnecessary human escalations.

### Analytics & Processing
* **`risk.py`**  
  A safety net module containing rule-based keyword scanning logic. It instantly detects critical issues (e.g., fraud, security breaches, legal threats) and forces an immediate escalation, bypassing the LLM to ensure safety.
  
* **`classifier.py`**  
  A lightweight helper module containing logic to determine product/module responsibilities and basic keyword-based request typing.
  
* **`utils.py`**  
  Contains essential utility functions, primarily focusing on robust JSON parsing. It gracefully handles malformed LLM responses and ensures the pipeline never crashes during string-to-dictionary conversion, providing a safe "escalated" fallback if parsing fails.

---

## 🚀 Usage

To execute the pipeline and process the support tickets, ensure your `.env` file is properly configured at the root of the project, then run:

```bash
python code/main.py
```

*(Optional)* If the `data/` document corpus has been modified, you should update the embedding cache by running:
```bash
python code/build_index.py
```
