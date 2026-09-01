#!/bin/bash
# Nightly backup for the AI research system. Run as root via cron.
set -euo pipefail
DEST=/opt/backups
KEEP_DAYS=7
D=$(date +%F_%H%M)
mkdir -p "$DEST"
log() { echo "$(date -Is) $*"; }

# 1. Magec config: agents, flows, MCP wiring, LLM backends + project secrets
tar czf "$DEST/magec-config-$D.tar.gz" -C / \
  root/magec/config.yaml root/magec/docker-compose.yaml root/magec/data/store.json \
  opt/research/.env
log "magec config + .env"

# 2. Custom MCP server source
tar czf "$DEST/mcp-src-$D.tar.gz" -C / root/fetch-mcp root/reddit-mcp
log "mcp source"

# 3. Magec database (long-term memory)
docker exec magec-postgres-1 pg_dump -U magec -d magec | gzip > "$DEST/db-magec-$D.sql.gz"
log "magec db"

# 4. Research database (Sindi pgvector store)
docker exec research_postgres pg_dump -U research_user -d research_db | gzip > "$DEST/db-research-$D.sql.gz"
log "research db"

# 5. prune
find "$DEST" -type f -name "*.gz" -mtime +$KEEP_DAYS -delete
log "pruned > $KEEP_DAYS days"
log "BACKUP COMPLETE $D ($(du -sh $DEST | cut -f1) total in $DEST)"
