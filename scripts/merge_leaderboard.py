#!/usr/bin/env python3
import json, urllib.request, os, re

NTFY = "https://ntfy.sh/wenxue-zhuangyuan-lb-2026/json?poll=1&since=all"
PATH = "leaderboard.json"
LEVELS = {"幼稚園", "小學", "初中", "高中", "大學", "碩士", "博士", "—"}


def sanitize(r):
    if not isinstance(r, dict):
        return None
    name = str(r.get("name") or "").strip()[:12]
    try:
        score = float(r.get("score"))
    except (TypeError, ValueError):
        return None
    if len(name) < 1 or score < 0 or score > 1e8:
        return None
    level = str(r.get("level") or "—")[:20]
    if level not in LEVELS and not re.match(r"^[\w\u4e00-\u9fff·\s]{1,20}$", level):
        level = "—"
    return {
        "name": name,
        "score": int(round(score)),
        "level": level,
        "date": str(r.get("date") or "")[:32],
    }


def load_existing():
    if not os.path.exists(PATH):
        return []
    try:
        data = json.load(open(PATH, encoding="utf-8"))
        if isinstance(data, list):
            return data
        return data.get("list") or []
    except Exception:
        return []


def fetch_ntfy():
    req = urllib.request.Request(NTFY, headers={"User-Agent": "wenxue-leaderboard"})
    with urllib.request.urlopen(req, timeout=30) as res:
        text = res.read().decode("utf-8", "replace")
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("event") != "message" or not ev.get("message"):
            continue
        msg = ev["message"]
        try:
            payload = json.loads(msg) if isinstance(msg, str) else msg
        except json.JSONDecodeError:
            continue
        out.append(payload)
    return out


def merge(lists):
    best = {}
    for lst in lists:
        for raw in lst:
            r = sanitize(raw)
            if not r:
                continue
            prev = best.get(r["name"])
            if not prev or r["score"] > prev["score"]:
                best[r["name"]] = r
    return sorted(best.values(), key=lambda x: x["score"], reverse=True)[:30]


def main():
    existing = load_existing()
    try:
        incoming = fetch_ntfy()
    except Exception as e:
        print("ntfy fetch failed:", e)
        incoming = []
    merged = merge([existing, incoming])
    json.dump({"list": merged}, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("wrote", len(merged), "rows")


if __name__ == "__main__":
    main()
