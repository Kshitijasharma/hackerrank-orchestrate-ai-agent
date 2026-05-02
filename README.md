# HackerRank Orchestrate

**HackerRank Orchestrate** 24-hour hackathon (May 1–2, 2026).

Goal : Build a terminal-based AI agent that triages real support tickets across three product ecosystems; **HackerRank**, **Claude**, and **Visa** — using only the support corpus shipped in this repo.

Problem Statement :  [`problem_statement.md`](./problem_statement.md)

# 🤖 HackerRank Orchestrate AI Agent

An intelligent **terminal-based AI support agent** that triages and responds to real-world support tickets across:

- 🧑‍💻 HackerRank  
- 🤖 Claude  
- 💳 Visa  

Built in a **24-hour hackathon**, this system combines **RAG (Retrieval-Augmented Generation), LLM reasoning, and safety guardrails** to produce **accurate, grounded, and reliable responses**.

---

<img width="2816" height="1368" alt="Gemini_Generated_Image_luiqx7luiqx7luiq" src="https://github.com/user-attachments/assets/6e9dd440-6553-40f4-abaa-15e245cc9a49" />



## 🎯 Problem

Support tickets are:

* noisy
* ambiguous
* sometimes risky (fraud, billing, account access)

The challenge:

Convert messy user queries into **structured decisions + safe responses** using ONLY the provided support corpus.

---

## 🧠 Solution Overview

We designed a **hybrid AI system** that combines:

* 🔍 Retrieval (RAG) → fetch relevant support docs
* 🤖 LLM reasoning → understand & generate responses
* ⚖️ Rule-based safety layer → enforce escalation for high-risk cases

---

## ⚙️ System Architecture

Checkout :   [`README.md`](./code/README.md)

```text
User Ticket
   ↓
Preprocessing (subject + issue)
   ↓
Hybrid Retrieval (Dense + Sparse)
   ↓
LLM Reasoning (classification + response)
   ↓
Safety Layer (risk override)
   ↓
Structured Output (CSV)
```

---

## ⚡ Demo

**Input Ticket:**

> "My Visa card was charged twice for the same transaction"

**Output:**

* Status: `escalated`
* Product Area: `billing`
* Request Type: `product_issue`

**Response:**
Duplicate charges may indicate a billing issue or transaction error. Please contact your issuing bank to initiate a chargeback...

**Justification:**
High financial risk detected → escalation required

---

## 🔍 Key Features

### ✅ Hybrid Retrieval (RAG)

* Dense (embeddings) + Sparse (TF-IDF)
* Improves relevance and reduces hallucination

### ✅ Structured AI Reasoning

* Outputs strict JSON:

  * `status`
  * `product_area`
  * `response`
  * `justification`
  * `request_type`

### ✅ Safety-First Design

* Fraud / billing / security → auto escalation
* Prevents unsafe or incorrect responses

### ✅ Cost Optimization

* Precomputed embeddings (cached locally)
* Reduced token usage drastically

### ✅ Deterministic Overrides

* Combines LLM intelligence with rule-based control

---

## 📂 Repository Structure

```text
.
├── AGENTS.md                       # Rules for AI coding tools + transcript logging
├── problem_statement.md            # Full task description and I/O schema
├── README.md                       
├── code/                           
│   └── main.py                     #   Entry point
│   └── build_index.py
│   └── classifier.py
│   └── llm.py
│   └── processor.py
│   └── retriever.py
│   └── risk.py
│   └── temp.py
│   └── utils.py
├── data/                           # Local-only support corpus (no network needed)
│   ├── hackerrank/                 #   HackerRank help center
│   ├── claude/                     #   Claude Help Center export
│   └── visa/                       #   Visa consumer + small-business support
│   └── embeddings.npy
└── support_tickets/
    ├── sample_support_tickets.csv  # Inputs + expected outputs (for development)
    ├── support_tickets.csv         # Inputs only (run your agent on these)
    └── output.csv                  # RESULTs
```

---

## 🧾 Output Format

Each ticket produces:

| Column          | Description               |
| --------------- | ------------------------- |
| `status`        | replied / escalated       |
| `product_area`  | domain classification     |
| `response`      | grounded user answer      |
| `justification` | reasoning behind decision |
| `request_type`  | issue classification      |

---

## 🚀 Quickstart

```bash
git clone https://github.com/Kshitijasharma/hackerrank-orchestrate-ai-agent.git
cd hackerrank-orchestrate-ai-agent/code
python main.py


```

---

## 🔒 Constraints

* Uses ONLY local support corpus (no external knowledge)
* Avoids hallucinations
* Escalates high-risk cases safely

---

## 📊 Results

Final outputs available at:

```bash
support_tickets/output.csv
```

---

## 🧠 Key Learnings

* LLMs need **retrieval + constraints** to be reliable
* Pure AI → unsafe
* Hybrid systems → production-ready

---

## 🏁 Hackathon

Built for **HackerRank Orchestrate (May 2026)**
Results announced: **May 15, 2026**

---

## ✨ Author

**Kshitija Sharma**

---

## ⭐ If you found this interesting

Give it a star ⭐ and explore the architecture!

