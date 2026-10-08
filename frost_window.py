import argparse
import datetime as dt
import json
import statistics
import sys
import urllib.parse
import urllib.request

GEO = "https://geocoding-api.open-meteo.com/v1/search?"
ARCHIVE = "https://archive-api.open-meteo.com/v1/archive?"
OLLAMA = "http://localhost:11434/api/generate"


def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode())


def locate(place):
    q = get(GEO + urllib.parse.urlencode({"name": place, "count": 1}))
    if not q.get("results"):
        sys.exit(f"Place not found: {place}")
    r = q["results"][0]
    return r["name"], r.get("country", ""), r["latitude"], r["longitude"]


def daily_min(lat, lon, years):
    end = dt.date.today() - dt.timedelta(days=7)
    start = dt.date(end.year - years, 1, 1)
    d = get(ARCHIVE + urllib.parse.urlencode({
        "latitude": lat, "longitude": lon,
        "start_date": start.isoformat(), "end_date": end.isoformat(),
        "daily": "temperature_2m_min", "timezone": "auto"}))
    return list(zip(d["daily"]["time"], d["daily"]["temperature_2m_min"]))


SHIFT = dt.timedelta(days=182)


def frost_dates(rows, threshold, south=False):
    by_year = {}
    for day, t in rows:
        if t is None:
            continue
        d = dt.date.fromisoformat(day)
        if south:
            d = d + SHIFT
        by_year.setdefault(d.year, []).append((d, t))
    last_spring, first_fall, seasons = [], [], 0
    for _, days in sorted(by_year.items()):
        if len(days) < 330:
            continue
        seasons += 1
        spring = [d for d, t in days if t <= threshold and d.month <= 6]
        fall = [d for d, t in days if t <= threshold and d.month >= 7]
        if spring:
            last_spring.append(spring[-1].timetuple().tm_yday)
        if fall:
            first_fall.append(fall[0].timetuple().tm_yday)
    return last_spring, first_fall, seasons


def pct(vals, p):
    s = sorted(vals)
    k = (len(s) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def doy(n, year, south=False):
    d = dt.date(year, 1, 1) + dt.timedelta(days=round(n) - 1)
    if south:
        d = d - SHIFT
    return d.strftime("%b %d")


def summarize(place, rows, threshold, south=False):
    spring, fall, seasons = frost_dates(rows, threshold, south)
    y = dt.date.today().year
    out = {"place": place, "years": seasons, "frost_years": len(fall),
           "spring_frost_years": len(spring), "threshold_c": threshold}
    if spring:
        out["last_spring_frost"] = {"median": doy(statistics.median(spring), y, south),
                                    "safe_90": doy(pct(spring, 0.9), y, south)}
    if fall:
        today = (dt.date.today() + (SHIFT if south else dt.timedelta(0))).timetuple().tm_yday
        out["first_fall_frost"] = {"early_10": doy(pct(fall, 0.1), y, south),
                                   "median": doy(statistics.median(fall), y, south)}
        out["chance_frost_by_next_week"] = round(sum(f <= today + 7 for f in fall) / len(fall), 2)
        out["days_until_median_first_frost"] = round(statistics.median(fall) - today)
    return out


def facts(s):
    out = []
    ff = s.get("first_fall_frost")
    if s["years"] and s["frost_years"] < s["years"] / 2:
        out.append(f"Frost is rare here: it happened in only {s['frost_years']} of the past {s['years']} years.")
        ff = None
    if ff:
        p = s["chance_frost_by_next_week"]
        d = s["days_until_median_first_frost"]
        if p == 0:
            out.append(f"No frost in the next 7 days in any of the past {s['years']} years.")
        else:
            out.append(f"Frost by next week happened in {round(p * 100)}% of past years.")
        if d > 0:
            out.append(f"Typical first frost is in about {d} days ({ff['median']}); an early year is {ff['early_10']}.")
            if d <= 21:
                out.append("Harvest tender crops (tomatoes, basil, peppers) soon.")
            if 14 <= d <= 45:
                out.append("This is garlic and tulip planting season.")
        else:
            out.append("First frost has usually already arrived by now.")
    ls = s.get("last_spring_frost")
    if ls and s["spring_frost_years"] < s["years"] / 2:
        ls = None
    if ls:
        out.append(f"Next spring, frost-tender seedlings are safe outside after {ls['safe_90']} in 9 of 10 years.")
    return out


def plan(summary, model):
    lines = facts(summary)
    prompt = (
        f"You are a friendly outdoors coach for {summary['place']}. "
        "Write exactly 4 short lines: 3 things to do outside this week and 1 line on what to plant or protect. "
        "Use ONLY these facts and do not contradict them:\n- " + "\n- ".join(lines)
    )
    body = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read().decode())["response"].strip()


def main():
    ap = argparse.ArgumentParser(description="Frost Window: local frost odds + an offline outdoor plan")
    ap.add_argument("place")
    ap.add_argument("--years", type=int, default=30)
    ap.add_argument("--threshold", type=float, default=0.0)
    ap.add_argument("--model", default="gemma3:4b")
    ap.add_argument("--no-llm", action="store_true")
    a = ap.parse_args()
    name, country, lat, lon = locate(a.place)
    print(f"Fetching {a.years} years of daily lows for {name}, {country} ...", flush=True)
    s = summarize(f"{name}, {country}", daily_min(lat, lon, a.years), a.threshold, south=lat < 0)
    print(json.dumps(s, indent=2))
    print("\nFacts:\n- " + "\n- ".join(facts(s)))
    if not a.no_llm:
        print(f"\nThis week's outdoor plan ({a.model}, running locally):\n")
        print(plan(s, a.model))


if __name__ == "__main__":
    main()
