"""Gera refresh token com escopo de edição e grava no .env desta skill (sem imprimir o token).
Uso: python3 oauth_login.py ga4|gtm   → imprime o link; esperar o usuário autorizar."""
import http.server, json, os, re, secrets, sys, urllib.parse, urllib.request
from _google import ENV_PATH, env

KINDS = {
    "ga4": ("GA4_REFRESH_TOKEN", ["https://www.googleapis.com/auth/analytics.edit",
                                  "https://www.googleapis.com/auth/analytics.readonly"]),
    "gtm": ("GTM_REFRESH_TOKEN", ["https://www.googleapis.com/auth/tagmanager.edit.containers",
                                  "https://www.googleapis.com/auth/tagmanager.edit.containerversions",
                                  "https://www.googleapis.com/auth/tagmanager.publish",
                                  "https://www.googleapis.com/auth/tagmanager.readonly"]),
}
VAR, SCOPES = KINDS[sys.argv[1]]
PORT = 8765
REDIRECT = f"http://127.0.0.1:{PORT}/"
e = env()
CID, CS = e["GOOGLE_ADS_CLIENT_ID"], e["GOOGLE_ADS_CLIENT_SECRET"]
STATE = secrets.token_urlsafe(16)
print("ABRA ESTE LINK:\n" + "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
    "client_id": CID, "redirect_uri": REDIRECT, "response_type": "code", "scope": " ".join(SCOPES),
    "access_type": "offline", "prompt": "consent", "state": STATE}), flush=True)


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if "code" not in q or q.get("state", [""])[0] != STATE:
            self.send_response(400); self.end_headers(); return
        r = json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", urllib.parse.urlencode({
            "code": q["code"][0], "client_id": CID, "client_secret": CS, "redirect_uri": REDIRECT,
            "grant_type": "authorization_code"}).encode()))
        rt = r.get("refresh_token")
        if rt:
            txt = open(ENV_PATH).read() if os.path.exists(ENV_PATH) else ""
            if re.search(rf"^{VAR}=.*$", txt, re.M):
                txt = re.sub(rf"^{VAR}=.*$", lambda m: f"{VAR}={rt}", txt, flags=re.M)
            else:
                txt = txt.rstrip("\n") + f"\n{VAR}={rt}\n"
            open(ENV_PATH, "w").write(txt)
            msg = f"OK: {VAR} salvo no .env. Escopos: {r.get('scope', '')}"
        else:
            msg = "ERRO: sem refresh_token na resposta"
        print(msg, flush=True)
        self.send_response(200); self.send_header("Content-Type", "text/plain; charset=utf-8"); self.end_headers()
        self.wfile.write("Pronto. Pode fechar esta aba.".encode())
        raise SystemExit


srv = http.server.HTTPServer(("127.0.0.1", PORT), H)
while True:
    try:
        srv.handle_request()
    except SystemExit:
        break
