import json
from frost_window import locate, daily_min, summarize, facts, plan

CITIES = ["Seoul", "Minneapolis", "London", "Toronto", "Denver", "Sapporo", "Berlin", "Melbourne"]
out = []
for c in CITIES:
    name, country, lat, lon = locate(c)
    s = summarize(f"{name}, {country}", daily_min(lat, lon, 30), 0.0, south=lat < 0)
    s["facts"] = facts(s)
    s["plan"] = plan(s, "gemma3:4b")
    out.append(s)
    print("done", c, flush=True)
json.dump(out, open("docs/demo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
