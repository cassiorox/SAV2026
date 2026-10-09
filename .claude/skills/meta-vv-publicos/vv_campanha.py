"""Cria publicos de VIDEO VIEW a partir dos videos dos anuncios de uma campanha.

Complemento do vv_publicos.py: em vez de varrer o Instagram organico, a fonte
sao os criativos dos anuncios de campanhas especificas -- util para "quem assistiu
75% do video daquela campanha da cidade X". A view PAGA conta na regra de
engajamento da Meta, entao o publico captura exatamente a audiencia da campanha.

Configuracao: o mesmo .env do vv_publicos.py (so precisa do META_TOKEN).

Exemplos:
  python vv_campanha.py --contas act_123 --campanha "CAMPANHA DE AQUECIMENTO" --dry-run
  python vv_campanha.py --contas act_123,act_456 --campanha 120210000000000000 --retencoes 75,95 --janela 90
"""
import argparse, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

G = "https://graph.facebook.com/v21.0"
HERE = os.path.dirname(os.path.abspath(__file__))
MAX_VIDS = 100     # teto da Meta de videos por regra (erro 2654)
MAX_MATCHES = 5    # freio: termo generico pode casar com centenas de campanhas

EV = {"3s": "video_watched", "15s": "video_view_15s",
      "25": "video_view_25_percent", "50": "video_view_50_percent",
      "75": "video_view_75_percent", "95": "video_completed"}
EV_LABEL = {"3s": "3s", "15s": "ThruPlay", "25": "25%", "50": "50%", "75": "75%", "95": "95%"}

# tags estruturais comuns em nome de campanha, removidas do nome do publico
NOISE_TAGS = "\\[(CBO|ABO|COMPRAS|VENDAS|LEADS|VV|V\\.VIEW|TR[A\xc1]FEGO|ALCANCE|ENGAJAMENTO|CONVERSAS)\\]"


# ---------- config ----------
def read_env():
    env = {}
    path = os.path.join(HERE, ".env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"')
    if os.environ.get("META_TOKEN"):
        env["META_TOKEN"] = os.environ["META_TOKEN"]
    return env


# ---------- Graph API ----------
def api(path, params=None, data=None, token=None, tries=5):
    if data is not None:
        body = urllib.parse.urlencode(dict(data, access_token=token)).encode()
        url = "%s/%s" % (G, path)
    else:
        body = None
        url = "%s/%s?%s" % (G, path, urllib.parse.urlencode(dict(params or {}, access_token=token)))
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=body), timeout=300) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read()).get("error", {})
            except Exception:
                err = {"message": str(e)}
            if err.get("code") in (17, 32, 4, 613, 80003, 80004) and i < tries - 1:
                print("  rate limit, aguardando 90s...", flush=True)
                time.sleep(90)
                continue
            return {"_error": err}
        except Exception as e:
            if i < tries - 1:
                time.sleep(15 * (i + 1))
                continue
            return {"_error": {"message": str(e)}}


def err_msg(res):
    e = res.get("_error", {})
    return "%s %s" % (e.get("code"), (e.get("error_user_msg") or e.get("message", ""))[:130])


def paginate(res):
    while True:
        for item in res.get("data", []):
            yield item
        nxt = res.get("paging", {}).get("next")
        if not nxt:
            return
        with urllib.request.urlopen(nxt, timeout=180) as r:
            res = json.load(r)


def existing_names(acct, token):
    res = api("%s/customaudiences" % acct, {"fields": "id,name", "limit": 500}, token=token)
    if "_error" in res:
        print("AVISO: nao consegui listar publicos de %s (%s); dedupe desligado" % (acct, err_msg(res)))
        return {}
    return {a["name"]: a["id"] for a in paginate(res)}


# ---------- campanhas ----------
def _norm(s):
    """Busca ignora colchetes: '[ALCANCE] SHOW' e 'ALCANCE SHOW' casam igual."""
    return re.sub(r"\s+", " ", s.replace("[", " ").replace("]", " ")).strip().lower()


def camp_short(name):
    """Tira tags estruturais do nome da campanha e mantem o resto (cidade/data)."""
    s = re.sub(NOISE_TAGS, " ", name, flags=re.I)
    s = s.replace("[", " ").replace("]", " ")
    return re.sub(r"\s+", " ", s).strip()[:45].strip() or name[:45]


def find_campaigns(contas, needle, token):
    """needle numerico = id direto; senao busca substring (sem colchetes) nas contas."""
    if needle.isdigit():
        res = api(needle, {"fields": "id,name,account_id"}, token=token)
        if "_error" in res:
            raise SystemExit("campanha %s: %s" % (needle, err_msg(res)))
        return [res]
    found, low = [], _norm(needle)
    for acct in contas:
        res = api("%s/campaigns" % acct, {"fields": "id,name,account_id", "limit": 300}, token=token)
        if "_error" in res:
            print("AVISO %s: %s" % (acct, err_msg(res)))
            continue
        found += [c for c in paginate(res) if low in _norm(c["name"])]
    return found


def campaign_videos(cid, token):
    """Extrai video_ids dos criativos dos anuncios (inclui dynamic creative)."""
    fields = "name,creative{video_id,object_story_spec,asset_feed_spec,effective_instagram_media_id}"
    res = api("%s/ads" % cid, {"fields": fields, "limit": 250}, token=token)
    if "_error" in res:
        raise SystemExit("ads de %s: %s" % (cid, err_msg(res)))
    vids, ig_fallback = [], []
    for ad in res.get("data", []):
        cr = ad.get("creative") or {}
        got = False
        if cr.get("video_id"):
            vids.append(cr["video_id"]); got = True
        vd = ((cr.get("object_story_spec") or {}).get("video_data") or {})
        if vd.get("video_id"):
            vids.append(vd["video_id"]); got = True
        for v in ((cr.get("asset_feed_spec") or {}).get("videos") or []):
            if v.get("video_id"):
                vids.append(v["video_id"]); got = True
        if not got and cr.get("effective_instagram_media_id"):
            ig_fallback.append(cr["effective_instagram_media_id"])
    if ig_fallback:
        print("  ! %d anuncio(s) 'publicacao existente' do IG (sem video_id) -- incluindo a midia IG;"
              " se nao for video, a Meta ignora na regra" % len(ig_fallback))
        vids += ig_fallback
    return sorted(set(vids))


# ---------- main ----------
def main():
    ap = argparse.ArgumentParser(description="Publicos de video view a partir dos anuncios de uma campanha")
    ap.add_argument("--contas", required=True, help="IDs de conta de anuncio separados por virgula (act_...)")
    ap.add_argument("--campanha", required=True, help="id numerico OU trecho do nome da campanha")
    ap.add_argument("--retencoes", default="75", help="combinacao de: 3s,15s,25,50,75,95 (default 75)")
    ap.add_argument("--janela", type=int, default=365, help="retencao em dias, 1-365 (default 365)")
    ap.add_argument("--dry-run", action="store_true", help="mostra o que seria criado, sem criar")
    a = ap.parse_args()

    env = read_env()
    tok = env.get("META_TOKEN")
    if not tok:
        raise SystemExit("META_TOKEN nao configurado. Crie um .env ao lado do script (veja .env.example).")
    contas = [c.strip() for c in a.contas.split(",") if c.strip()]
    bad = [c for c in contas if not c.startswith("act_")]
    if bad:
        raise SystemExit("IDs de conta devem comecar com act_: %s" % bad)
    retencoes = [r.strip() for r in a.retencoes.split(",")]
    bad = [r for r in retencoes if r not in EV]
    if bad:
        raise SystemExit("retencao invalida %s (validas: %s)" % (bad, list(EV)))
    if not 1 <= a.janela <= 365:
        raise SystemExit("--janela deve estar entre 1 e 365 (limite da Meta)")

    camps = find_campaigns(contas, a.campanha, tok)
    if not camps:
        raise SystemExit("nenhuma campanha com '%s' nas contas informadas" % a.campanha)
    if len(camps) > MAX_MATCHES:
        print("'%s' casou com %d campanhas -- termo generico demais." % (a.campanha, len(camps)))
        print("Primeiras 20 (use um trecho mais especifico ou o id):")
        for c in camps[:20]:
            print("  %s  %s" % (c["id"], c["name"][:70]))
        raise SystemExit(1)
    print("%d campanha(s): %s" % (len(camps), "; ".join(c["name"][:60] for c in camps)))

    for c in camps:
        vids = campaign_videos(c["id"], tok)
        if not vids:
            print("[%s] 0 videos nos criativos -- pulando" % c["name"][:50])
            continue
        extra = ""
        if len(vids) > MAX_VIDS:
            extra = " (primeiros %d de %d)" % (MAX_VIDS, len(vids))
            vids = vids[:MAX_VIDS]
        print("[%s] %d video(s)%s" % (c["name"][:50], len(vids), extra))
        short = camp_short(c["name"])
        for ret in retencoes:
            name = "VIDEOVIEW %s | ADS %s" % (EV_LABEL[ret], short)
            if a.janela != 365:
                name += " | %dD" % a.janela
            desc = "%d videos dos anuncios da campanha %s (%s) - retencao %dd" % (
                len(vids), c["name"][:80], c["id"], a.janela)
            rule = json.dumps([{"object_id": v, "event_name": EV[ret]} for v in vids])
            for acct in contas:
                if a.dry_run:
                    print("[dry-run] %s: criaria '%s' (%d videos)" % (acct, name, len(vids)))
                    continue
                if name in existing_names(acct, tok):
                    print("ja existe: %s %s" % (acct, name))
                    continue
                res = api("%s/customaudiences" % acct, data={
                    "name": name, "subtype": "ENGAGEMENT", "retention_days": a.janela,
                    "rule": rule, "prefill": "true", "description": desc}, token=tok)
                time.sleep(1)
                print("%s %s: %s" % ("OK" if "_error" not in res else "ERRO " + err_msg(res), acct, name), flush=True)


if __name__ == "__main__":
    main()
