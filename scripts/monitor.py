#!/usr/bin/env python3
"""Health monitor for the AI research system. Cron every ~10 min. SILENCE = ISSUE."""
import json, subprocess, time, urllib.request, urllib.error, os, glob

OUT = "/root/monitor"; os.makedirs(OUT, exist_ok=True)
checks = []
def add(name, ok, detail=""): checks.append({"check": name, "ok": bool(ok), "detail": str(detail)[:120]})

def sh(args, timeout=12):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as e:
        return 1, str(e)[:120]

def http(url, timeout=8):
    try:
        r = urllib.request.urlopen(url, timeout=timeout); return True, "HTTP %s" % r.status
    except urllib.error.HTTPError as e:
        return e.code in (200,401,403,404,405), "HTTP %s" % e.code
    except Exception as e:
        return False, str(e)[:120]

# 1. containers running
for c in ["magec-magec-1","magec-postgres-1","magec-ollama-1","magec-fetch-mcp-1","research_postgres"]:
    rc, out = sh(["docker","inspect","-f","{{.State.Running}}",c])
    add("container:"+c, rc==0 and out.startswith("true"), out)

# 2. Magec API up
add("magec-api", *http("http://localhost:8081/"))

# 3. databases accepting connections
rc,out = sh(["docker","exec","magec-postgres-1","pg_isready","-U","magec"]);      add("db:magec", rc==0, out)
rc,out = sh(["docker","exec","research_postgres","pg_isready","-U","research_user"]); add("db:research", rc==0, out)

# 4. Ollama daemon (needed for embeddings)
rc,out = sh(["docker","exec","magec-ollama-1","ollama","list"]); add("ollama", rc==0, out.splitlines()[0] if out else "")

# 5. Tavily remote MCP reachable
add("mcp:tavily-remote", *http("https://mcp.tavily.com/", timeout=10))

# 6. backup freshness (newest file in /opt/backups < 26h old)
fs = glob.glob("/opt/backups/*")
if fs:
    age_h = (time.time() - max(os.path.getmtime(f) for f in fs)) / 3600
    add("backup-fresh", age_h < 26, "newest %.1fh old" % age_h)
else:
    add("backup-fresh", False, "no backups found")

# 7. disk space
rc,out = sh(["df","--output=pcent","/"]); 
try:
    pct = int(out.split()[-1].rstrip("%")); add("disk", pct < 90, "%d%% used" % pct)
except Exception:
    add("disk", False, out)

failed = [c for c in checks if not c["ok"]]
status = {
  "time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
  "overall": "OK" if not failed else "DEGRADED",
  "failed": [c["check"] for c in failed],
  "checks": checks,
}
json.dump(status, open(OUT+"/status.json","w"), indent=2)
line = "%s  %s  %s" % (status["time"], status["overall"],
                       "all ok" if not failed else "FAIL: " + ", ".join(status["failed"]))
open(OUT+"/monitor.log","a").write(line + "\n")
print(line)
if failed:
    for c in failed: print("  ALERT %s -> %s" % (c["check"], c["detail"]))
raise SystemExit(1 if failed else 0)
