"""GA4 via Admin API.
  ticket  --name "Nome do Cliente"            → link de aceite dos termos; espera o redirect e imprime o accountId (rodar em background)
  setup   --account ID --property-name "X - Site" --site https://... --ads 1234567890 [--category OTHER] [--key-event lead_form]
  status  --property ID                        → medição otimizada + indicadores do Google
  list                                         → contas acessíveis"""
import argparse, http.server, json, urllib.parse
from _google import ga_admin, need

p = argparse.ArgumentParser()
sub = p.add_subparsers(dest="cmd", required=True)
t = sub.add_parser("ticket"); t.add_argument("--name", required=True); t.add_argument("--region", default="BR")
s = sub.add_parser("setup")
for a in ("--account", "--property-name", "--site", "--ads"):
    s.add_argument(a, required=True)
s.add_argument("--category", default="OTHER"); s.add_argument("--key-event", default="lead_form")
s.add_argument("--timezone", default="America/Sao_Paulo"); s.add_argument("--currency", default="BRL")
st = sub.add_parser("status"); st.add_argument("--property", required=True)
sub.add_parser("list")
a = p.parse_args()
api = ga_admin()

if a.cmd == "list":
    for x in need(api.call("GET", "v1beta/accountSummaries?pageSize=200"), "list").get("accountSummaries", []):
        print(x["account"], "|", x.get("displayName"), "|", [(q["property"], q["displayName"]) for q in x.get("propertySummaries", [])])

elif a.cmd == "ticket":
    r = need(api.call("POST", "v1beta/accounts:provisionAccountTicket",
                      {"account": {"displayName": a.name, "regionCode": a.region}, "redirectUri": "http://127.0.0.1:8765/"}), "ticket")
    print("ACEITE OS TERMOS:\nhttps://analytics.google.com/analytics/web/?provisioningSignup=false#/termsofservice/" + r["accountTicketId"], flush=True)

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *x):
            pass

        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            print("CONTA CRIADA: accountId =", q.get("accountId", ["?"])[0], flush=True)
            self.send_response(200); self.send_header("Content-Type", "text/plain; charset=utf-8"); self.end_headers()
            self.wfile.write("Conta criada. Pode fechar esta aba.".encode())
            raise SystemExit

    srv = http.server.HTTPServer(("127.0.0.1", 8765), H)
    while True:
        try:
            srv.handle_request()
        except SystemExit:
            break

elif a.cmd == "setup":
    prop = need(api.call("POST", "v1beta/properties", {"parent": f"accounts/{a.account}", "displayName": a.property_name,
                "timeZone": a.timezone, "currencyCode": a.currency, "industryCategory": a.category}), "propriedade")
    pid = prop["name"]
    stream = need(api.call("POST", f"v1beta/{pid}/dataStreams", {"type": "WEB_DATA_STREAM", "displayName": urllib.parse.urlparse(a.site).netloc,
                  "webStreamData": {"defaultUri": a.site}}), "fluxo web")
    need(api.call("PATCH", f"v1beta/{pid}/dataRetentionSettings?updateMask=eventDataRetention,resetUserDataOnNewActivity",
                  {"eventDataRetention": "FOURTEEN_MONTHS", "resetUserDataOnNewActivity": True}), "retenção")
    need(api.call("POST", f"v1beta/{pid}/keyEvents", {"eventName": a.key_event, "countingMethod": "ONCE_PER_EVENT"}), "evento-chave")
    link = need(api.call("POST", f"v1beta/{pid}/googleAdsLinks", {"customerId": a.ads.replace("-", ""), "adsPersonalizationEnabled": True}), "vínculo Ads")
    print(json.dumps({"property": pid, "stream": stream["name"], "measurementId": stream["webStreamData"]["measurementId"],
                      "keyEvent": a.key_event, "adsLink": link["name"]}, indent=1))

elif a.cmd == "status":
    pid = f"properties/{a.property}"
    streams = need(api.call("GET", f"v1beta/{pid}/dataStreams"), "fluxos").get("dataStreams", [])
    for sm in streams:
        em = api.call("GET", f"v1alpha/{sm['name']}/enhancedMeasurementSettings")
        print(sm["name"], sm.get("webStreamData", {}).get("measurementId"), "| medição otimizada:",
              {k: v for k, v in em.items() if k.endswith("Enabled")})
    print("indicadores do Google:", api.call("GET", f"v1alpha/{pid}/googleSignalsSettings").get("state"))
    print("eventos-chave:", [k["eventName"] for k in api.call("GET", f"v1beta/{pid}/keyEvents").get("keyEvents", [])])
