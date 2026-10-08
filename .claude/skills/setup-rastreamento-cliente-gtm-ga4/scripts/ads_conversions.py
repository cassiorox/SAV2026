"""Cria as conversões padrão no Google Ads e imprime o send_to de cada uma.
  create --customer 1234567890 [--call-seconds 60] [--sem-maps] [--sem-chamada]
  list   --customer 1234567890
Padrão: Lead formulario (lead_form) principal · Chamada pelo anuncio principal · Clique WhatsApp e Como chegar secundárias.
Usa o SDK e o .env da skill google-ads (GOOGLE_ADS_*)."""
import argparse, os, re, sys
from _google import ROOT

sys.path.insert(0, os.path.join(ROOT, ".claude/skills/google-ads/scripts"))
from lib import init_client  # noqa: E402

p = argparse.ArgumentParser()
sub = p.add_subparsers(dest="cmd", required=True)
c = sub.add_parser("create"); c.add_argument("--customer", required=True); c.add_argument("--call-seconds", type=int, default=60)
c.add_argument("--sem-maps", action="store_true"); c.add_argument("--sem-chamada", action="store_true")
l = sub.add_parser("list"); l.add_argument("--customer", required=True)
a = p.parse_args()
cid = a.customer.replace("-", "")
client = init_client()
E = client.enums


def create(name, type_, category, primary, call_seconds=None):
    svc = client.get_service("ConversionActionService")
    op = client.get_type("ConversionActionOperation"); ca = op.create
    ca.name = name; ca.type_ = type_; ca.category = category
    ca.status = E.ConversionActionStatusEnum.ENABLED
    ca.counting_type = E.ConversionActionCountingTypeEnum.ONE_PER_CLICK
    ca.primary_for_goal = primary
    ca.click_through_lookback_window_days = 30
    ca.value_settings.default_value = 1; ca.value_settings.always_use_default_value = True
    ca.value_settings.default_currency_code = "BRL"
    if call_seconds:
        ca.phone_call_duration_seconds = call_seconds
    try:
        print("criada:", svc.mutate_conversion_actions(customer_id=cid, operations=[op]).results[0].resource_name, "|", name)
    except Exception as e:
        print("ERRO:", name, str(e)[:300])


if a.cmd == "create":
    W = E.ConversionActionTypeEnum.WEBPAGE
    Cat = E.ConversionActionCategoryEnum
    create("Lead formulario (lead_form)", W, Cat.SUBMIT_LEAD_FORM, True)
    create("Clique WhatsApp", W, Cat.CONTACT, False)
    if not a.sem_maps:
        create("Como chegar", W, Cat.GET_DIRECTIONS, False)
    if not a.sem_chamada:
        create(f"Chamada pelo anuncio ({a.call_seconds}s+)", E.ConversionActionTypeEnum.AD_CALL, Cat.PHONE_CALL_LEAD, True, a.call_seconds)

ga = client.get_service("GoogleAdsService")
q = ("SELECT conversion_action.id, conversion_action.name, conversion_action.type, conversion_action.status, "
     "conversion_action.primary_for_goal, conversion_action.tag_snippets FROM conversion_action")
print("\nid | nome | tipo | status | meta | send_to")
for b in ga.search_stream(customer_id=cid, query=q):
    for r in b.results:
        x = r.conversion_action; st = None
        for ts in x.tag_snippets:
            m = re.search(r"'send_to': '([^']+)'", ts.event_snippet or "")
            if m:
                st = m.group(1); break
        print(x.id, "|", x.name, "|", x.type_.name, "|", x.status.name, "|", "principal" if x.primary_for_goal else "secundaria", "|", st)
