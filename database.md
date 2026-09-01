# Database Setup — Phase 0

## Connection Details

- **Host:** 169.58.211.103
- **Port:** 5432
- **Database:** research_db
- **User:** research_user
- **Password:** research_secure_password_123

## Table Schema

### documents table
- `id` (SERIAL PRIMARY KEY)
- `question` (TEXT NOT NULL)
- `answer` (TEXT NOT NULL)
- `source_urls` (TEXT[] array)
- `embedding` (vector(1536))
- `created_at` (TIMESTAMP, default CURRENT_TIMESTAMP)

### Indexes
- IVFFlat index on embedding column for fast similarity search

## Setup Instructions

### 1. Start Docker container
```bash
cd /opt/research
docker compose up -d
```

### 2. Build pgvector from source
```bash
docker compose exec postgres bash
apt-get update
apt-get install -y postgresql-server-dev-16 gcc g++ make git
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
make install
exit
docker compose restart postgres
```

### 3. Create extension and schema
```bash
docker compose exec -T postgres psql -U research_user -d research_db << 'EOF'
CREATE EXTENSION vector;

CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  source_urls TEXT[] DEFAULT ARRAY[]::TEXT[],
  embedding vector(1536),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
EOF
```

### 4. Test queries
```bash
# Insert test row
docker compose exec -T postgres psql -U research_user -d research_db << 'EOF'
INSERT INTO documents (question, answer, source_urls, embedding)
VALUES (
  'What is climate change?',
  'Climate change refers to long-term shifts in global temperatures.',
  ARRAY['https://example.com/climate'],
  ('[' || array_to_string(array_fill(0.0, ARRAY[1536]), ',') || ']')::vector(1536)
);
EOF

# Read it back
docker compose exec -T postgres psql -U research_user -d research_db -c "SELECT id, question FROM documents WHERE id = 1;"

# Vector similarity query
docker compose exec -T postgres psql -U research_user -d research_db -c "SELECT id, question, 1 - (embedding <=> '[0.1, 0.2, 0.3]'::vector(1536)) AS similarity FROM documents ORDER BY similarity DESC LIMIT 1;"
```

## Embedding Model

Vector size: **1536** (default for OpenAI text-embedding-3-small)

## Status

- [x] Docker container running
- [x] pgvector extension built and enabled
- [x] documents table created
- [x] IVFFlat index created
- [x] Test insert/read passed
- [x] Vector similarity query tested
- [x] Connection verified from VPS
