"""Cria publicos de VIDEO VIEW do Instagram na Meta, por retencao/ano/corte de views.

Versao standalone para compartilhamento — sem dependencias alem do Python 3.9+.

Como funciona:
  1. Lista as paginas de Facebook que o seu token administra (me/accounts)
  2. Acha o Instagram business vinculado a cada pagina
  3. Varre os videos do IG e guarda os que tem N+ views (cache local retomavel)
  4. Cria na(s) conta(s) de anuncio um publico de engajamento por retencao
     (3s / ThruPlay / 25% / 50% / 75% / 95%), com os top videos de cada ano (max 100 por regra)

Configuracao: arquivo .env ao lado deste script (veja .env.example) ou variaveis
de ambiente META_TOKEN / META_INSIGHTS_TOKEN.

Exemplos:
  python vv_publicos.py --contas act_123 --retencoes 75,95 --anos 2025,2026 --min-views 100000 --dry-run
  python vv_publicos.py --contas act_123,act_456 --paginas "Minha Pagina" --retencoes 75 --anos 2026
"""
import argparse, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

G = "https://graph.facebook.com/v21.0"
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(HERE, "vv_cache.json")
MAX_VIDS = 100  # teto da Meta de videos por regra de publico (erro 2654 acima disso)

EV = {"3s": "video_watched", "15s": "video_view_15s",
      "25": "video_view_25_percent", "50": "video_view_50_percent",
      "75": "video_view_75_percent", "95": "video_completed"}
EV_LABEL = {"3s": "3s", "15s": "ThruPlay", "25": "25%", "50": "50%", "75": "75%", "95": "95%"}


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
    for k in ("META_TOKEN", "META_INSIGHTS_TOKEN"):
        if os.environ.get(k):
            env[k] = os.environ[k]
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
            # rate limit: espera e tenta de novo
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


# ---------- cache ----------
def load_cache():
    if os.path.exists(CACHE_FILE):
        return json.load(open(CACHE_FILE, encoding="utf-8"))
    return {}


def save_cache(c):
    json.dump(c, open(CACHE_FILE, "w", encoding="utf-8"))


# ---------- varredura ----------
def harvest(page, min_views, since, cache):
    """Varre os videos do IG da pagina e guarda os com min_views+ no cache."""
    iba = (page.get("instagram_business_account") or {}).get("id")
    if not iba:
        print("[%s] sem Instagram business vinculado, pulando" % page["name"])
        return
    pt = page["access_token"]
    key = "%s|%s" % (min_views, iba)
    if cache.get(key, {}).get("done"):
        print("[%s] cache: %d videos qualificados" % (page["name"], len(cache[key]["qualified"])))
        return
    user = api(iba, {"fields": "username"}, token=pt).get("username", "?")
    entry = cache.setdefault(key, {"username": user, "qualified": []})
    seen = {q["id"] for q in entry["qualified"]}
    res = api("%s/media" % iba, {"fields": "id,media_type,timestamp", "limit": 50, "since": since}, token=pt)
    scanned = 0
    while True:
        if "_error" in res:
            print("[%s] ERRO lendo media: %s" % (page["name"], err_msg(res)))
            break
        batch = res.get("data", [])
        if not batch:
            break
        stop = False
        for m in batch:
            ts = m.get("timestamp", "")
            if ts and ts[:10] < since:
                stop = True
                break
            if m.get("media_type") != "VIDEO" or m["id"] in seen:
                continue
            ins = api("%s/insights" % m["id"], {"metric": "views"}, token=pt)
            time.sleep(0.25)
            scanned += 1
            if scanned % 50 == 0:
                print("  ... %d videos analisados" % scanned, flush=True)
            if "_error" not in ins and ins.get("data"):
                v = ins["data"][0]["values"][0].get("value") or 0
                if v >= min_views:
                    entry["qualified"].append({"id": m["id"], "ts": ts[:10], "views": v})
        save_cache(cache)
        nxt = res.get("paging", {}).get("next")
        if stop or not nxt:
            break
        with urllib.request.urlopen(nxt, timeout=180) as r:
            res = json.load(r)
    entry["done"] = True
    save_cache(cache)
    print("[%s] @%s: %d videos com %s+ views" % (page["name"], user, len(entry["qualified"]), fmt_int(min_views)))


def fmt_int(n):
    return ("{:,}".format(n)).replace(",", ".")


# ---------- main ----------
def main():
    ap = argparse.ArgumentParser(description="Cria publicos de video view do Instagram na Meta")
    ap.add_argument("--contas", required=True, help="IDs de conta de anuncio separados por virgula (act_...)")
    ap.add_argument("--paginas", help="nomes de pagina FB separados por ; (default: todas com IG do seu token)")
    ap.add_argument("--retencoes", default="75,95", help="combinacao de: 3s,15s,25,50,75,95 (default 75,95)")
    ap.add_argument("--anos", default=None, help="anos separados por virgula (default: ano atual)")
    ap.add_argument("--min-views", type=int, default=100000, help="corte minimo de views (default 100000)")
    ap.add_argument("--janela", type=int, default=365, help="retencao em dias, 1-365 (default 365)")
    ap.add_argument("--dry-run", action="store_true", help="mostra o que seria criado, sem criar")
    a = ap.parse_args()

    if not 1 <= a.janela <= 365:
        raise SystemExit("--janela deve estar entre 1 e 365 (limite da Meta)")

    env = read_env()
    ads_tok = env.get("META_TOKEN")
    if not ads_tok:
        raise SystemExit("META_TOKEN nao configurado. Crie um .env ao lado do script (veja .env.example).")
    ins_tok = env.get("META_INSIGHTS_TOKEN") or ads_tok

    contas = [c.strip() for c in a.contas.split(",") if c.strip()]
    bad = [c for c in contas if not c.startswith("act_")]
    if bad:
        raise SystemExit("IDs de conta devem comecar com act_: %s" % bad)
    retencoes = [r.strip() for r in a.retencoes.split(",")]
    bad = [r for r in retencoes if r not in EV]
    if bad:
        raise SystemExit("retencao invalida %s (validas: %s)" % (bad, list(EV)))
    anos = [y.strip() for y in a.anos.split(",")] if a.anos else [time.strftime("%Y")]
    since = min(anos) + "-01-01"

    # paginas administradas pelo token de insights
    res = api("me/accounts", {"fields": "id,name,access_token,instagram_business_account", "limit": 100}, token=ins_tok)
    if "_error" in res:
        raise SystemExit("Erro listando paginas (me/accounts): %s" % err_msg(res))
    pages = list(paginate(res))
    if a.paginas:
        wanted = [p.strip().lower() for p in a.paginas.split(";")]
        pages = [p for p in pages if p["name"].lower() in wanted]
        if not pages:
            raise SystemExit("Nenhuma pagina do token bate com --paginas. Disponiveis: %s" % [p["name"] for p in res.get("data", [])])
    else:
        pages = [p for p in pages if p.get("instagram_business_account")]
        if not pages:
            raise SystemExit("Nenhuma pagina com Instagram vinculado neste token.")
    print("Paginas: %s" % ", ".join(p["name"] for p in pages))
    print("Contas: %s | retencoes %s | anos %s | %s+ views%s" % (
        ", ".join(contas), retencoes, anos, fmt_int(a.min_views), " | DRY-RUN" if a.dry_run else ""))
    print("")

    cache = load_cache()
    for p in pages:
        harvest(p, a.min_views, since, cache)

    # junta qualificados de todas as paginas varridas neste corte
    quals, handles = [], set()
    for key, e in cache.items():
        if key.startswith("%s|" % a.min_views) and e.get("done"):
            quals += e["qualified"]
            if e.get("qualified"):
                handles.add("@" + e.get("username", "?"))
    handles = sorted(handles)

    print("")
    for ano in anos:
        year_q = sorted({q["id"]: q for q in quals if q["ts"][:4] == ano}.values(), key=lambda q: -q["views"])
        if not year_q:
            print("%s: nenhum video qualificado" % ano)
            continue
        vids = [q["id"] for q in year_q[:MAX_VIDS]]
        extra = " (top %d de %d por views)" % (len(vids), len(year_q)) if len(year_q) > len(vids) else ""
        for ret in retencoes:
            name = "VIDEOVIEW %s | IG %s | %dk+ views" % (EV_LABEL[ret], ano, a.min_views // 1000)
            if a.janela != 365:
                name += " | %dD" % a.janela
            desc = "%d videos (%s) publicados em %s com %s+ views%s - retencao %dd" % (
                len(vids), ", ".join(handles), ano, fmt_int(a.min_views), extra, a.janela)
            rule = json.dumps([{"object_id": v, "event_name": EV[ret]} for v in vids])
            for acct in contas:
                if a.dry_run:
                    print("[dry-run] %s: criaria '%s' (%d videos%s)" % (acct, name, len(vids), extra))
                    continue
                if name in existing_names(acct, ads_tok):
                    print("ja existe: %s %s" % (acct, name))
                    continue
                res = api("%s/customaudiences" % acct, data={
                    "name": name, "subtype": "ENGAGEMENT", "retention_days": a.janela,
                    "rule": rule, "prefill": "true", "description": desc}, token=ads_tok)
                time.sleep(1)
                print("%s %s: %s" % ("OK" if "_error" not in res else "ERRO " + err_msg(res), acct, name), flush=True)


if __name__ == "__main__":
    main()
