#!/usr/bin/env python3
"""
Run one research question through the Magec pipeline (Researcher -> Critic -> Writer)
and save the finished report into the research database (research_db.documents).

Usage:
  python3 pipeline_run.py "your question here"
  python3 pipeline_run.py --topics scripts/topics.txt      # run the next unused topic
"""
import json, os, sys, time, urllib.request, uuid, re
import psycopg2

# ---------------------------------------------------------------------------
# Config: read secrets/paths from /opt/research/.env  (one KEY=value per line)
# ---------------------------------------------------------------------------
def env(key, default=""):
    try:
        for line in open("/opt/research/.env"):
            if line.startswith(key + "="):
                return line.rstrip("\n").split("=", 1)[1] or default
    except FileNotFoundError:
        pass
    return default

MAGEC_API = "http://localhost:8080/api/v1"
CLIENT_TOKEN = "mgc_e2741353bce3a031abc5262c48fd760bcefbf0bf"   # test-librarian client
FLOW_ID = "00d035fb-dff6-4248-8c1f-a5c0cd6fbe66"               # research-pipeline flow
OLLAMA = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"

DB = dict(
    host=env("POSTGRES_HOST", "localhost"),
    port=env("POSTGRES_PORT", "5432"),
    dbname=env("POSTGRES_DB", "research_db"),
    user=env("POSTGRES_USER", "research_user"),
    password=env("POSTGRES_PASSWORD"),
)

# ---------------------------------------------------------------------------
# Small HTTP helper: POST json, return parsed json
# ---------------------------------------------------------------------------
def post(url, body, headers=None, timeout=600):
    data = json.dumps(body).encode()
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    return json.load(urllib.request.urlopen(req, timeout=timeout))

# ---------------------------------------------------------------------------
# 1. Run the pipeline through Magec's REST API
# ---------------------------------------------------------------------------
def run_pipeline(question):
    session = "run-" + uuid.uuid4().hex[:8]
    auth = {"Authorization": "Bearer " + CLIENT_TOKEN}
    # create a session for the flow
    post(f"{MAGEC_API}/agent/apps/{FLOW_ID}/users/sara/sessions/{session}", {}, auth)
    # send the question, get back the list of events (everything each agent did)
    events = post(f"{MAGEC_API}/agent/run", {
        "appName": FLOW_ID, "userId": "sara", "sessionId": session,
        "newMessage": {"role": "user", "parts": [{"text": question}]},
    }, auth)

    # collect the final text from each agent  (agent_1=Researcher, _2=Critic, _3=Writer)
    text_by_agent = {}
    for e in events:
        who = e.get("author", "?")
        for part in (e.get("content") or {}).get("parts", []):
            if part.get("text") and not part.get("thought"):
                text_by_agent[who] = text_by_agent.get(who, "") + part["text"]
    return text_by_agent

# ---------------------------------------------------------------------------
# 2. Turn the report text into a 768-number embedding (local Ollama, free)
# ---------------------------------------------------------------------------
def embed(text):
    r = post(f"{OLLAMA}/api/embeddings",
             {"model": EMBED_MODEL, "prompt": text[:8000]}, timeout=60)
    return r["embedding"]

# ---------------------------------------------------------------------------
# 3. Save one row into research_db.documents
# ---------------------------------------------------------------------------
def save_report(question, report, source_urls, vector):
    conn = psycopg2.connect(**DB)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """INSERT INTO documents (question, answer, source_urls, embedding)
                   VALUES (%s, %s, %s, %s) RETURNING id""",
                (question, report, source_urls, vector),
            )
            new_id = cur.fetchone()[0]
        return new_id
    finally:
        conn.close()

# pull "http(s)://..." links out of the report text
def find_urls(text):
    urls = re.findall(r"https?://[^\s\]\)\}】>]+", text)
    seen, out = set(), []
    for u in urls:
        u = u.rstrip(".,;")
        if u not in seen:
            seen.add(u); out.append(u)
    return out

# ---------------------------------------------------------------------------
# topics file: run the next line that has no "# done" marker
# ---------------------------------------------------------------------------
def next_topic(path):
    lines = open(path).read().split("\n")
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s and not s.startswith("#"):
            lines[i] = "# done " + time.strftime("%Y-%m-%d") + "  " + s
            open(path, "w").write("\n".join(lines))
            return s
    return None

# ---------------------------------------------------------------------------
def main():
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] == "--topics":
        question = next_topic(args[1])
        if not question:
            print("no unused topics left in", args[1]); return
    elif args:
        question = " ".join(args)
    else:
        print(__doc__); return

    print(f"[{time.strftime('%H:%M:%S')}] question: {question}")
    t0 = time.time()
    out = run_pipeline(question)
    report = out.get("agent_3") or out.get("Writer") or ""
    if not report:
        print("!! no report produced. agent outputs:", list(out))
        sys.exit(1)

    sources = find_urls(out.get("agent_1", "") + "\n" + report)
    vector = embed(report)
    row_id = save_report(question, report, sources, vector)

    print(f"[{time.strftime('%H:%M:%S')}] done in {time.time()-t0:.0f}s")
    print(f"  saved as documents.id = {row_id}")
    print(f"  {len(sources)} source links, report {len(report)} chars")

if __name__ == "__main__":
    main()
