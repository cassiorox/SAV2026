"""Tempo real do GA4 (últimos 30 min) por evento e evento-chave.
Uso: python3 realtime.py --property 123456789 [--need page_view lead_form]  (exit 0 quando todos os --need apareceram)"""
import argparse, sys
from _google import ga_data, need

p = argparse.ArgumentParser(); p.add_argument("--property", required=True); p.add_argument("--need", nargs="*", default=[])
a = p.parse_args()
api = ga_data()
r = need(api.call("POST", f"properties/{a.property}:runRealtimeReport", {"dimensions": [{"name": "eventName"}],
         "metrics": [{"name": "eventCount"}, {"name": "keyEvents"}], "minuteRanges": [{"startMinutesAgo": 29, "endMinutesAgo": 0}]}), "realtime")
rows = {x["dimensionValues"][0]["value"]: (x["metricValues"][0]["value"], x["metricValues"][1]["value"]) for x in r.get("rows", [])}
for ev, (n, k) in sorted(rows.items()):
    print(f"{ev:24} eventos={n:>4}  eventos-chave={k}")
if not rows:
    print("sem eventos nos últimos 30 min")
sys.exit(0 if all(n in rows for n in a.need) else 1)
