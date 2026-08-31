# AI Research System

Finds, verifies, analyses, and explains useful information and opportunities.
First target: EU grant calls open for small AI startups.

## Flow

```
Web / APIs
   -> Magec + AI agents
   -> Research -> Analyse -> Verify
   -> PostgreSQL + pgvector   (memory)
   -> Final report
```

## Team

| Person  | Owns                                   |
|---------|----------------------------------------|
| Sara    | VPS / hosting                          |
| Sindi   | database (PostgreSQL + pgvector)       |
| Lediona | agents (Magec, LLM, agent design)      |

## Tools

| Tool                    | Job                                          |
|-------------------------|----------------------------------------------|
| VPS                     | always-on host                               |
| Magec                   | runs and manages the AI agents               |
| LLM                     | reads text and explains it                   |
| PostgreSQL + pgvector   | knowledge store, searchable by meaning       |
| n8n                     | automation and scheduled runs                |
| LangGraph               | complex, multi-step agent workflows          |
| Critic / Contradictor   | agent that checks results for holes          |

## Setup

```bash
cp .env.example .env   # then fill in real values — never commit .env
```

Real secret values are shared through Bitwarden, not through Git.
