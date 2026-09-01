#!/usr/bin/env python3
import json, sys, time, urllib.request, uuid

BASE  = "http://localhost:8080/api/v1"
TOKEN = "mgc_e2741353bce3a031abc5262c48fd760bcefbf0bf"
FLOW  = "00d035fb-dff6-4248-8c1f-a5c0cd6fbe66"

def run(text):
    sess = "q-" + uuid.uuid4().hex[:8]
    urllib.request.urlopen(urllib.request.Request(
        BASE + "/agent/apps/" + FLOW + "/users/sara/sessions/" + sess,
        data=b"{}", headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"},
        method="POST"))
    body = json.dumps({"appName": FLOW, "userId": "sara", "sessionId": sess,
                       "newMessage": {"role": "user", "parts": [{"text": text}]}}).encode()
    r = urllib.request.urlopen(urllib.request.Request(
        BASE + "/agent/run", data=body,
        headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"},
        method="POST"), timeout=600)
    for e in json.load(r):
        auth = e.get("author", "?")
        for p in (e.get("content") or {}).get("parts", []):
            if p.get("thought"):
                continue
            t = p.get("text")
            if t:
                print("\n=== " + auth + " ===\n" + t)
            fc = p.get("functionCall")
            if fc:
                print("\n[" + auth + " -> tool: " + str(fc.get("name")) + " " + json.dumps(fc.get("args", {}))[:200] + "]")
            frp = p.get("functionResponse")
            if frp:
                out = json.dumps(frp.get("response", {}))
                print("\n[tool result: " + out[:300] + "]")

q = sys.argv[1] if len(sys.argv) > 1 else "What EU grant calls are currently open for small AI startups?"
print("QUESTION:", q)
t = time.time()
run(q)
print("\n--- done in %.0fs ---" % (time.time() - t))
