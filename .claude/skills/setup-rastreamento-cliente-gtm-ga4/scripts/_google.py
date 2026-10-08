"""Helpers comuns: lê as credenciais, troca refresh token por access token e faz chamadas REST.
Nunca imprime tokens.

Credenciais (a primeira que tiver a chave vence):
  1. variáveis de ambiente
  2. .env desta skill (GA4_REFRESH_TOKEN, GTM_REFRESH_TOKEN, gravados pelo oauth_login.py)
  3. .env da skill google-ads (GOOGLE_ADS_CLIENT_ID, GOOGLE_ADS_CLIENT_SECRET)"""
import json, os, time, urllib.error, urllib.parse, urllib.request

SKILL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT = os.path.abspath(os.path.join(SKILL_DIR, "../../.."))
ENV_PATH = os.path.join(SKILL_DIR, ".env")
ENV_FILES = [ENV_PATH,
             os.path.join(ROOT, ".claude/skills/google-ads/.env"),
             os.path.expanduser("~/.claude/skills/google-ads/.env")]


def _read(path):
    out = {}
    if not os.path.exists(path):
        return out
    for line in open(path):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            v = v.strip().strip("\"'")
            if v:
                out[k.strip()] = v
    return out


def env():
    out = {}
    for path in reversed(ENV_FILES):
        out.update(_read(path))
    out.update({k: v for k, v in os.environ.items() if k.startswith(("GOOGLE_ADS_", "GA4_", "GTM_")) and v})
    return out


def access_token(var):
    e = env()
    falta = [k for k in ("GOOGLE_ADS_CLIENT_ID", "GOOGLE_ADS_CLIENT_SECRET", var) if k not in e]
    if falta:
        raise SystemExit(f"Faltam credenciais: {falta}. Client ID/Secret vêm do .env da skill google-ads; "
                         f"o {var} é gerado por: python3 scripts/oauth_login.py {'ga4' if var.startswith('GA4') else 'gtm'}")
    data = urllib.parse.urlencode({"client_id": e["GOOGLE_ADS_CLIENT_ID"], "client_secret": e["GOOGLE_ADS_CLIENT_SECRET"],
                                   "refresh_token": e[var], "grant_type": "refresh_token"}).encode()
    r = json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", data))
    return r["access_token"], r.get("scope", "")


class Api:
    def __init__(self, base, token_var):
        self.base = base
        self.at, self.scope = access_token(token_var)

    def call(self, method, path, body=None):
        url = path if path.startswith("http") else self.base + path
        data = json.dumps(body).encode() if body is not None else (b"" if method == "POST" else None)
        req = urllib.request.Request(url, data=data, method=method,
                                     headers={"Authorization": "Bearer " + self.at, "Content-Type": "application/json"})
        for tentativa in range(6):
            try:
                raw = urllib.request.urlopen(req).read()
                return json.loads(raw) if raw else {}
            except urllib.error.HTTPError as e:
                body = e.read().decode()[:800]
                # 429 por minuto (GTM: ~15 req/min por usuário) → espera e tenta de novo; cota diária não adianta esperar
                if e.code == 429 and "per day" not in body and tentativa < 5:
                    time.sleep(20 * (tentativa + 1)); continue
                return {"ERROR": e.code, "body": body}


def ga_admin():
    return Api("https://analyticsadmin.googleapis.com/", "GA4_REFRESH_TOKEN")


def ga_data():
    return Api("https://analyticsdata.googleapis.com/v1beta/", "GA4_REFRESH_TOKEN")


def gtm():
    return Api("https://tagmanager.googleapis.com/tagmanager/v2/", "GTM_REFRESH_TOKEN")


def need(r, what):
    if isinstance(r, dict) and "ERROR" in r:
        raise SystemExit(f"ERRO em {what}: {r}")
    return r
