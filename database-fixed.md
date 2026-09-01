# Database Setup — Phase 0

## Connection Details

- **Host:** 169.58.211.103
- **Port:** 5432
- **Database:** research_db
- **User:** research_user
- **Password:** [in shared secret place, not in repo]

## Vector Size

768 (nomic-embed-text)

## Docker Image

pgvector/pgvector:pg16 (extension included, persistent)

## Table Schema

### documents table
- `id` (SERIAL PRIMARY KEY)
- `question` (TEXT NOT NULL)
- `answer` (TEXT NOT NULL)
- `source_urls` (TEXT[] array)
- `embedding` (vector(768))
- `created_at` (TIMESTAMP, default CURRENT_TIMESTAMP)

### Indexes
- IVFFlat index on embedding column for fast similarity search

## Status

- [x] Docker container running (pgvector/pgvector:pg16)
- [x] documents table created with vector(768)
- [x] pgvector extension enabled
- [x] Test insert/read passed
