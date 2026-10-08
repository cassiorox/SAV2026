"""Monta o container GTM padrão via Tag Manager API (GTM_REFRESH_TOKEN), num workspace novo, sem publicar.
  find    --public-id GTM-XXXXXXX
  build   --public-id GTM-XXXXXXX --ga4 G-XXXXXXXXXX --aw 1234567890 --label-lead X --label-wpp Y [--label-maps Z]
          [--exclude-text "Abrir WhatsApp"] [--workspace-name "Setup inicial IA"]
  publish --workspace accounts/A/containers/C/workspaces/W --name "v1 - Setup inicial GA4 + Google Ads" [--notes "..."]
Contrato do dataLayer esperado: {event:'lead_form', pagina, convenio, telefone:'+55...'}"""
import argparse
from _google import gtm, need

p = argparse.ArgumentParser()
sub = p.add_subparsers(dest="cmd", required=True)
f = sub.add_parser("find"); f.add_argument("--public-id", required=True); f.add_argument("--account-id")
b = sub.add_parser("build")
for x in ("--public-id", "--ga4", "--aw", "--label-lead", "--label-wpp"):
    b.add_argument(x, required=True)
b.add_argument("--label-maps"); b.add_argument("--exclude-text", default="Abrir WhatsApp"); b.add_argument("--account-id")
b.add_argument("--workspace-name", default="Setup inicial IA")
pb = sub.add_parser("publish"); pb.add_argument("--workspace", required=True); pb.add_argument("--name", required=True)
pb.add_argument("--notes", default="")
a = p.parse_args()
api = gtm()


def find(public_id, account_id=None):
    """Passe --account-id (número da conta do GTM, visível na URL da interface) para não varrer todas as contas."""
    accs = need(api.call("GET", "accounts"), "contas").get("account", [])
    if account_id:
        accs = [x for x in accs if x["accountId"] == account_id]
    for acc in accs:
        for c in need(api.call("GET", f"accounts/{acc['accountId']}/containers"), "containers").get("container", []):
            if c["publicId"] == public_id:
                return acc, c
    raise SystemExit(f"{public_id} não encontrado. A conta do GTM foi criada com o mesmo login do GTM_REFRESH_TOKEN?")


if a.cmd == "find":
    acc, c = find(a.public_id, a.account_id)
    print(acc["accountId"], acc["name"], "|", c["path"], c["publicId"], c["name"], c.get("usageContext"))
    for w in api.call("GET", f"{c['path']}/workspaces").get("workspace", []):
        print("  workspace", w["path"], w["name"])
    raise SystemExit

if a.cmd == "publish":
    r = need(api.call("POST", f"{a.workspace}:create_version", {"name": a.name, "notes": a.notes}), "versão")
    if r.get("compilerError"):
        raise SystemExit(f"erro de compilação: {r}")
    v = r["containerVersion"]
    need(api.call("POST", f"{v['path']}:publish"), "publicação")
    print("publicada versão", v["containerVersionId"], v["name"], "|", len(v.get("tag", [])), "tags,",
          len(v.get("trigger", [])), "acionadores,", len(v.get("variable", [])), "variáveis")
    raise SystemExit

# build
acc, c = find(a.public_id, a.account_id)
existing = api.call("GET", f"{c['path']}/workspaces/{c.get('defaultWorkspaceId', '1')}/tags").get("tag", [])
if existing:
    print("ATENÇÃO: o container já tem tags no workspace padrão:", [t["name"] for t in existing])
ws = need(api.call("POST", f"{c['path']}/workspaces", {"name": a.workspace_name, "description": "GA4 + Google Ads + conversões otimizadas"}), "workspace")
W = ws["path"]; print("workspace", W)
AW = a.aw.replace("AW-", "")
T = lambda k, v: {"type": "template", "key": k, "value": v}
B = lambda k, v: {"type": "boolean", "key": k, "value": v}
ok = lambda r, w: (print("ok", w), r)[1] if "ERROR" not in r else need(r, w)

bi = ["clickElement", "clickClasses", "clickId", "clickTarget", "clickUrl", "clickText", "formElement", "formClasses", "formId",
      "formTarget", "formUrl", "formText", "scrollDepthThreshold", "scrollDepthUnits", "historySource", "newHistoryFragment",
      "oldHistoryFragment", "newHistoryState", "oldHistoryState"]
ok(api.call("POST", f"{W}/built_in_variables?" + "&".join("type=" + t for t in bi)), "19 variáveis integradas")
dlv = lambda key: [{"type": "integer", "key": "dataLayerVersion", "value": "2"}, B("setDefaultValue", "false"), T("name", key)]
for name, type_, params in [("CONST - GA4 Measurement ID", "c", [T("value", a.ga4)]), ("CONST - AW Conversion ID", "c", [T("value", "AW-" + AW)]),
                            ("DLV - telefone", "v", dlv("telefone")), ("DLV - pagina", "v", dlv("pagina")), ("DLV - convenio", "v", dlv("convenio")),
                            ("UPD - Lead (telefone)", "awec", [T("mode", "MANUAL"), T("phone_number", "{{DLV - telefone}}")])]:
    ok(api.call("POST", f"{W}/variables", {"name": name, "type": type_, "parameter": params}), name)


def cond(t, a0, a1, neg=False):
    ps = [T("arg0", a0), T("arg1", a1)] + ([B("negate", "true")] if neg else [])
    return {"type": t, "parameter": ps}


def trig(body):
    return ok(api.call("POST", f"{W}/triggers", body), body["name"])["triggerId"]


WRX = r"wa\.me|api\.whatsapp\.com|whatsapp\.com/send"
MRX = r"google\.[a-z.]+/maps|maps\.app\.goo\.gl|goo\.gl/maps|maps\.google|waze\.com"
link = lambda name, rx: {"name": name, "type": "linkClick", "filter": [cond("matchRegex", "{{Click URL}}", rx)],
                         "waitForTags": B("waitForTags", "false"), "checkValidation": B("checkValidation", "false")}
t_lead = trig({"name": "CE - lead_form", "type": "customEvent", "customEventFilter": [cond("equals", "{{_event}}", "lead_form")]})
t_wl = trig(link("Click - WhatsApp (link)", WRX))
btn = [cond("matchRegex", "{{Click Text}}", "(?i)whatsapp"), cond("matchRegex", "{{Click URL}}", WRX, True)]
if a.exclude_text:
    btn.append(cond("matchRegex", "{{Click Text}}", r"^\s*" + a.exclude_text + r"\s*$", True))
t_wb = trig({"name": "Click - WhatsApp (botao sem link)", "type": "click", "filter": btn})
t_wc = trig({"name": "CE - whatsapp_click", "type": "customEvent", "customEventFilter": [cond("matchRegex", "{{_event}}", "^(whatsapp_click|click_whatsapp)$")]})
t_m = trig(link("Click - Como chegar", MRX)) if a.label_maps else None

ALL = "2147479553"
params = lambda items: {"type": "list", "key": "eventParameters", "list": [{"type": "map", "map": [T("name", k), T("value", v)]} for k, v in items]}


def tag(name, type_, ps, triggers):
    ok(api.call("POST", f"{W}/tags", {"name": name, "type": type_, "parameter": ps, "firingTriggerId": triggers, "tagFiringOption": "oncePerEvent"}), name)


def ga4_event(name, event, items, triggers):
    tag(name, "gaawe", [T("eventName", event), T("measurementIdOverride", a.ga4), params(items)], triggers)


def ads(name, label, triggers, enhanced=False):
    ps = [T("conversionId", AW), T("conversionLabel", label), T("currencyCode", "BRL"), B("enableConversionLinker", "true")]
    if enhanced:
        ps += [B("enableEnhancedConversion", "true"), T("cssProvidedEnhancedConversionValue", "{{UPD - Lead (telefone)}}")]
    tag(name, "awct", ps, triggers)


tag("Google Tag - GA4", "googtag", [T("tagId", "{{CONST - GA4 Measurement ID}}")], [ALL])
tag("Conversion Linker", "gclidw", [B("enableCrossDomain", "false"), B("enableCookieOverrides", "false"), B("enableUrlPassthrough", "false")], [ALL])
ga4_event("GA4 - lead_form", "lead_form", [("pagina", "{{DLV - pagina}}"), ("convenio", "{{DLV - convenio}}"), ("page_location", "{{Page URL}}")], [t_lead])
ads("Ads - Lead formulario", a.label_lead, [t_lead], enhanced=True)
wpp = [t_wl, t_wb, t_wc]
ga4_event("GA4 - click_whatsapp", "click_whatsapp", [("link_url", "{{Click URL}}"), ("link_text", "{{Click Text}}"), ("page_location", "{{Page URL}}")], wpp)
ads("Ads - Clique WhatsApp", a.label_wpp, wpp)
if t_m:
    ga4_event("GA4 - click_como_chegar", "click_como_chegar", [("link_url", "{{Click URL}}"), ("page_location", "{{Page URL}}")], [t_m])
    ads("Ads - Como chegar", a.label_maps, [t_m])

qp = api.call("POST", f"{W}:quick_preview")
print("\ncompilerError:", qp.get("compilerError"), "| WORKSPACE:", W)
