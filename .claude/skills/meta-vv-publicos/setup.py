"""Setup guiado do meta-vv-publicos: valida o token na API, mostra suas contas
de anuncio e paginas (pra voce copiar os act_...) e cria o .env.

Uso:
  python setup.py                        interativo (cola o token quando pedir)
  python setup.py --token SEU_TOKEN      direto (ex.: quando o Claude Code roda por voce)
  python setup.py --insights-token OUTRO opcional: token separado so pros insights do IG
"""
import argparse, json, os, sys, urllib.error, urllib.parse, urllib.request

G = "https://graph.facebook.com/v21.0"
HERE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(HERE, ".env")

PERMS_ADS = {"ads_management"}
PERMS_ORGANICO = {"pages_show_list", "pages_read_engagement", "instagram_basic", "instagram_manage_insights"}


def get(path, params, token):
    url = "%s/%s?%s" % (G, path, urllib.parse.urlencode(dict(params, access_token=token)))
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            return {"_error": json.loads(e.read()).get("error", {})}
        except Exception:
            return {"_error": {"message": str(e)}}
    except Exception as e:
        return {"_error": {"message": str(e)}}


def fail(msg):
    print("\nX %s" % msg)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", help="token da Meta (senao, pede interativo)")
    ap.add_argument("--insights-token", help="opcional: token separado com as permissoes de IG")
    a = ap.parse_args()

    print("")
    print("=== meta-vv-publicos: setup ===")
    if sys.version_info < (3, 9):
        fail("Python 3.9+ necessario (voce tem %d.%d)." % sys.version_info[:2])
    print("ok Python %d.%d" % sys.version_info[:2])

    tok = (a.token or "").strip()
    if not tok:
        tok = input("\nCole seu token da Meta e aperte Enter: ").strip()
    if not tok:
        fail("nenhum token informado.")

    # 1. token valido?
    me = get("me", {"fields": "id,name"}, tok)
    if "_error" in me:
        fail("token recusado pela Meta: %s" % me["_error"].get("message", "?"))
    print("ok token valido (%s)" % me.get("name", me.get("id")))

    # 2. permissoes
    perms = get("me/permissions", {}, tok)
    granted = {p["permission"] for p in perms.get("data", []) if p.get("status") == "granted"}
    if granted:
        faltam_ads = PERMS_ADS - granted
        faltam_org = PERMS_ORGANICO - granted
        if faltam_ads:
            print("!! faltam permissoes pra CRIAR publicos: %s" % sorted(faltam_ads))
        else:
            print("ok permissoes de ads")
        if faltam_org:
            print("!! faltam pro modo ORGANICO (vv_publicos.py): %s" % sorted(faltam_org))
            print("   (o modo por campanha, vv_campanha.py, nao precisa delas)")
        else:
            print("ok permissoes de Instagram/paginas")
    else:
        print("!! nao consegui ler as permissoes (system user nao expoe) — seguindo")

    # 3. contas de anuncio
    accs = get("me/adaccounts", {"fields": "name", "limit": 50}, tok)
    if "_error" not in accs and accs.get("data"):
        print("\nSuas contas de anuncio (use no --contas):")
        for acc in accs["data"][:25]:
            print("  %-22s %s" % (acc["id"], acc.get("name", "")))
        primeira = accs["data"][0]["id"]
    else:
        print("\n!! nao consegui listar contas de anuncio (%s)" % err_txt(accs))
        primeira = "act_SEU_ID"

    # 4. paginas com IG (so relevante pro modo organico)
    pages = get("me/accounts", {"fields": "name,instagram_business_account", "limit": 50}, tok)
    if "_error" not in pages and pages.get("data"):
        com_ig = [p for p in pages["data"] if p.get("instagram_business_account")]
        print("\nPaginas com Instagram vinculado (modo organico):")
        for p in com_ig[:25]:
            print("  %s" % p["name"])
        if not com_ig:
            print("  (nenhuma — o modo organico nao vai achar videos)")
    else:
        print("\n!! nenhuma pagina visivel pro token (modo por campanha funciona mesmo assim)")

    # 5. escreve o .env
    lines = ["META_TOKEN=%s" % tok]
    if a.insights_token:
        lines.append("META_INSIGHTS_TOKEN=%s" % a.insights_token.strip())
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\nok .env criado em %s" % ENV_PATH)

    print("\nProximo passo (sempre com --dry-run primeiro):")
    print("  python vv_publicos.py --contas %s --retencoes 75,95 --min-views 100000 --dry-run" % primeira)
    print("  python vv_campanha.py --contas %s --campanha \"NOME DA CAMPANHA\" --dry-run" % primeira)
    print("")


def err_txt(res):
    return (res.get("_error", {}) or {}).get("message", "?")[:100]


if __name__ == "__main__":
    main()
