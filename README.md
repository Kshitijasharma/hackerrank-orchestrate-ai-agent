# HackerRank Orchestrate

**HackerRank Orchestrate** 24-hour hackathon (May 1–2, 2026).

Goal : Build a terminal-based AI agent that triages real support tickets across three product ecosystems; **HackerRank**, **Claude**, and **Visa** — using only the support corpus shipped in this repo.

Problem Statement :  [`problem_statement.md`](./problem_statement.md)

---
## Repository layout

```
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


Checkout [`README.md`](./code/README.md) inside /code for complete pipeline flow.


## Requirements: 

A terminal-based agent that, for each row in `support_tickets/support_tickets.csv`, produces:

| Column         | Allowed values                                          |
| -------------- | ------------------------------------------------------- |
| `status`       | `replied`, `escalated`                                  |
| `product_area` | most relevant support category / domain area            |
| `response`     | user-facing answer grounded in the provided corpus      |
| `justification`| concise explanation of the routing/answering decision   |
| `request_type` | `product_issue`, `feature_request`, `bug`, `invalid`    |

Hard requirements (from `problem_statement.md`):

- Must be **terminal-based**.
- Must use **only the provided support corpus** (no live web calls for ground-truth answers).
- Must **escalate** high-risk, sensitive, or unsupported cases instead of guessing.
- Must avoid hallucinated policies or unsupported claims.

Beyond that you are free to bring your own approach — RAG, vector DBs, tool use, structured output, agent frameworks, classical ML, or anything else.

---

## Core : 

All of your work belongs in [`code/`](./code/). The repo ships with an empty `code/main.py` you can grow into your full agent — add more modules (`agent.py`, `retriever.py`, `classifier.py`, etc.) next to it as needed.

Conventions:

- Written a **README inside `code/`** describing how to install dependencies and run your agent.
- Added keys(api) inside .env.
- Saved responses to `support_tickets/output.csv`.

---

## Quickstart

Clone this repository:

```bash
git clone https://github.com/Kshitijasharma/hackerrank-orchestrate-ai-agent.git
```
Used Python to build this proejct.

---

Results will be announced on May 15, 2026

---

## Results : 

Checkout support_tickets/output.csv. 

