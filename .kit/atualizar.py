#!/usr/bin/env python3
"""Atualiza o kit ClaudePRO sem sobrescrever nada do aluno.

Baixa a versao mais nova do repositorio oficial e compara arquivo por arquivo:
  novo        -> nao existe aqui: e adicionado
  atualizar   -> existe e o aluno nunca mexeu (bate com uma versao oficial): e substituido (com backup)
  revisar     -> existe e o aluno mexeu: NAO e tocado; a versao nova vai pra .kit/revisar/ pra mesclar
  personalizado -> o aluno mexeu, mas o kit nao mudou esse arquivo desde a ultima mesclagem: fica quieto
  protegido   -> contexto, marca, clientes, dados, credenciais: nunca e tocado
  apagado     -> o aluno apagou um arquivo do kit: continua apagado
  removido    -> saiu do kit oficial: so avisa, nao apaga nada aqui

Uso:
  python3 .kit/atualizar.py            # simulacao: mostra o que vai acontecer, nao muda nada
  python3 .kit/atualizar.py --aplicar  # aplica
  python3 .kit/atualizar.py --json     # saida em JSON (usada pela skill atualizar-kit)
  python3 .kit/atualizar.py --fonte <pasta>  # usa uma pasta local como versao nova (teste)

Protecao extra do aluno: .kit/protegidos-locais.txt, um caminho ou padrao por linha (ex: AGENTS.md,
.claude/skills/minha-skill/**). O que casar ali nunca e tocado.

So usa biblioteca padrao do Python. Nao depende de Git.
"""
import argparse, fnmatch, hashlib, io, json, shutil, sys, tarfile, tempfile, urllib.request
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
KIT = RAIZ / ".kit"
PADRAO = {
    "repositorio": "cassiorox/ClaudePRO",
    "branch": "main",
    "protegidos": ["_contexto/**", "marca/**", "clientes/**", "dados/**", ".env", "*.env", "contas.yaml"],
    "excecoes": ["clientes/_template/**", "clientes/README.md", "dados/README.md"],
}
SEMPRE_ATUALIZAR = {".kit/manifesto.json", ".kit/config.json"}


def ler_json(caminho, padrao=None):
    try:
        return json.loads(Path(caminho).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def blob_sha(dados):
    return hashlib.sha1(b"blob %d\0" % len(dados) + dados).hexdigest()


def hashes_locais(dados):
    """Hash como o Git calcularia, e tambem com quebra de linha normalizada (Windows grava CRLF)."""
    hs = {blob_sha(dados)}
    if b"\r\n" in dados:
        hs.add(blob_sha(dados.replace(b"\r\n", b"\n")))
    return hs


def casa(caminho, padroes):
    nome = caminho.rsplit("/", 1)[-1]
    for p in padroes:
        if p.endswith("/**"):
            if caminho.startswith(p[:-2]):
                return True
        elif "/" in p:
            if fnmatch.fnmatchcase(caminho, p):
                return True
        elif fnmatch.fnmatchcase(nome, p):
            return True
    return False


def ler_pasta(pasta):
    pasta = Path(pasta)
    return {p.relative_to(pasta).as_posix(): p.read_bytes() for p in pasta.rglob("*") if p.is_file()}


def baixar(repo, branch):
    url = f"https://codeload.github.com/{repo}/tar.gz/refs/heads/{branch}"
    with urllib.request.urlopen(url, timeout=60) as r:
        dados = r.read()
    with tarfile.open(fileobj=io.BytesIO(dados), mode="r:gz") as tar:
        membros = []
        for m in tar.getmembers():
            if not m.isfile():
                continue
            partes = Path(m.name).parts
            if len(partes) < 2 or ".." in partes or Path(m.name).is_absolute():
                continue
            membros.append(m)
        arquivos = {}
        for m in membros:
            rel = "/".join(Path(m.name).parts[1:])  # tira a pasta "Repo-main/"
            arquivos[rel] = tar.extractfile(m).read()
    return arquivos


def planejar(novos, cfg, manifesto_novo, manifesto_local):
    oficiais = {c: set(hs) for c, hs in manifesto_novo.get("arquivos", {}).items()}
    atual_antes = set((manifesto_local or {}).get("atual", []))
    plano = {k: [] for k in ("novo", "atualizar", "revisar", "personalizado", "protegido", "apagado", "removido", "igual")}

    for caminho, dados in sorted(novos.items()):
        local = RAIZ / caminho
        protegido = (casa(caminho, cfg["protegidos"]) and not casa(caminho, cfg["excecoes"])) or casa(caminho, cfg.get("locais", []))
        if caminho in SEMPRE_ATUALIZAR:
            plano["igual" if local.exists() and local.read_bytes() == dados else "atualizar"].append(caminho)
        elif protegido:
            plano["protegido"].append(caminho)
        elif not local.exists():
            plano["apagado" if caminho in atual_antes else "novo"].append(caminho)
        else:
            atuais = hashes_locais(local.read_bytes())
            if blob_sha(dados) in atuais:
                plano["igual"].append(caminho)
            elif atuais & (oficiais.get(caminho, set()) | {blob_sha(dados)}):
                plano["atualizar"].append(caminho)
            elif (KIT / "base" / caminho).is_file() and (KIT / "base" / caminho).read_bytes() == dados:
                plano["personalizado"].append(caminho)  # ja mesclado com esta versao oficial
            else:
                plano["revisar"].append(caminho)

    for caminho in sorted(atual_antes - set(novos)):
        if (RAIZ / caminho).exists():
            plano["removido"].append(caminho)
    return plano


def aplicar(plano, novos):
    carimbo = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup = KIT / "backup" / carimbo
    revisar = KIT / "revisar"
    if revisar.exists():
        shutil.rmtree(revisar)
    for caminho in plano["atualizar"]:
        local = RAIZ / caminho
        if local.exists() and caminho not in SEMPRE_ATUALIZAR:
            (backup / caminho).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local, backup / caminho)
    for caminho in plano["novo"] + plano["atualizar"]:
        local = RAIZ / caminho
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(novos[caminho])
    for caminho in plano["revisar"]:
        alvo = revisar / caminho
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_bytes(novos[caminho])
    return backup if backup.exists() else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fonte", help="pasta local com a versao nova (pra testar sem baixar)")
    a = ap.parse_args()

    cfg = {**PADRAO, **ler_json(KIT / "config.json", {})}
    manifesto_local = ler_json(KIT / "manifesto.json")
    try:
        novos = ler_pasta(a.fonte) if a.fonte else baixar(cfg["repositorio"], cfg["branch"])
    except Exception as e:
        sys.exit(f"Nao consegui baixar o kit de github.com/{cfg['repositorio']}: {e}")

    manifesto_novo = json.loads(novos.get(".kit/manifesto.json", b"{}") or b"{}")
    cfg_novo = json.loads(novos.get(".kit/config.json", b"{}") or b"{}")
    cfg = {**cfg, **{k: cfg_novo[k] for k in ("protegidos", "excecoes") if k in cfg_novo}}
    try:
        locais = (KIT / "protegidos-locais.txt").read_text(encoding="utf-8").splitlines()
        cfg["locais"] = [l.strip() for l in locais if l.strip() and not l.startswith("#")]
    except OSError:
        pass
    plano = planejar(novos, cfg, manifesto_novo, manifesto_local)

    resultado = {
        "versao_local": (manifesto_local or {}).get("versao"),
        "versao_nova": manifesto_novo.get("versao"),
        "aplicado": a.aplicar,
        "plano": {k: v for k, v in plano.items() if k != "igual"},
        "sem_mudanca": len(plano["igual"]) + len(plano["personalizado"]),
    }
    if a.aplicar:
        backup = aplicar(plano, novos)
        resultado["backup"] = str(backup.relative_to(RAIZ)) if backup else None
        resultado["revisar_em"] = ".kit/revisar/" if plano["revisar"] else None
        (KIT / "ultima-atualizacao.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=1))

    if a.json:
        print(json.dumps(resultado, ensure_ascii=False, indent=1))
        return

    rotulos = {
        "novo": "Novos (vao ser adicionados)",
        "atualizar": "Atualizados (voce nunca mexeu neles)",
        "revisar": "Voce mexeu: NAO vou sobrescrever, versao nova vai pra .kit/revisar/",
        "personalizado": "Personalizados por voce, sem novidade no kit: intocados",
        "protegido": "Protegidos (teu contexto, marca, clientes, credenciais): intocados",
        "apagado": "Voce apagou: continuam apagados",
        "removido": "Sairam do kit oficial: ficam aqui, apaga se quiser",
    }
    print(f"Kit local: {resultado['versao_local'] or 'desconhecida'}  ->  oficial: {resultado['versao_nova'] or '?'}")
    for k, rotulo in rotulos.items():
        if plano[k]:
            print(f"\n{rotulo} ({len(plano[k])}):")
            for c in plano[k][:40]:
                print(f"  {c}")
            if len(plano[k]) > 40:
                print(f"  ... e mais {len(plano[k]) - 40}")
    print(f"\nSem mudanca: {len(plano['igual'])} arquivos.")
    if plano["revisar"] and a.aplicar:
        print("Mesclar: compare cada arquivo com .kit/revisar/<caminho> (versao oficial nova) e, se existir,")
        print(".kit/base/<caminho> (versao oficial da ultima mesclagem). Depois mova a copia de revisar/ pra base/.")
    if not a.aplicar:
        print("\nSimulacao. Nada foi alterado. Rode com --aplicar pra atualizar.")
    elif resultado.get("backup"):
        print(f"\nBackup do que foi substituido: {resultado['backup']}")


if __name__ == "__main__":
    main()
