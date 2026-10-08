"""Confere o que o site entrega: snippet do GTM, evento lead_form e links. Baixa com curl (Cloudflare bloqueia Python).
Uso: python3 check_site.py https://site.com.br GTM-XXXXXXX"""
import re, subprocess, sys

url, gtm_id = sys.argv[1].rstrip("/"), sys.argv[2]
get = lambda u: subprocess.run(["curl", "-sL", "-A", "Mozilla/5.0", u], capture_output=True, text=True, errors="ignore").stdout
html = get(url + "/")
print("HTML bytes:", len(html))
print("snippet gtm.js com o ID:", bool(re.search(r"gtm\.js.{0,400}" + re.escape(gtm_id) + "|" + re.escape(gtm_id) + r".{0,40}", html, re.S)) and ("gtm.js" in html))
print("noscript ns.html com o ID:", f"ns.html?id={gtm_id}" in html)
print("gtag/GA/AW direto no HTML:", sorted(set(re.findall(r"gtag/js\?id=[\w-]+", html))) or "nenhum")
js = ""
for path in sorted(set(re.findall(r"/assets/[\w\-.]+\.js", html))):
    js += get(url + path) + "\n"
print("JS bytes:", len(js))
for k in ["lead_form", "eventCallback", "eventTimeout", "telefone", "gclid", "sessionStorage", "whatsapp_click", "wa.me",
          "google.com/maps", "maps.app.goo.gl", "waze.com"]:
    print(f"  {k:16} {js.count(k) + html.count(k)}")
for m in re.finditer(r"lead_form", js):
    print("\nTRECHO DO PUSH:\n", js[max(0, m.start() - 400):m.end() + 300])
for m in re.finditer(r"type:`button`[^}]{0,200}WhatsApp|Abrir WhatsApp|Não abriu", js):
    print("\nBOTÃO DE WHATSAPP SEM LINK (conferir se duplica clique):", js[max(0, m.start() - 150):m.end() + 60].replace("\n", " "))
