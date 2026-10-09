#!/usr/bin/env python3
"""Gera .kit/manifesto.json: para cada arquivo do kit, os hashes de TODAS as versoes que ja existiram
no historico do Git. O atualizador usa isso pra saber se o aluno mexeu num arquivo: se o hash do arquivo
dele bate com alguma versao oficial, ele nao mexeu e o arquivo pode ser atualizado com seguranca.

Uso (so no repositorio oficial, antes de publicar):
  python3 .kit/gerar_manifesto.py

O hook de pre-commit local roda isso sozinho e adiciona o manifesto ao commit.
"""
import json, subprocess
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / ".kit/manifesto.json"
IGNORAR = {".kit/manifesto.json"}


def git(*args):
    return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, check=True).stdout


def main():
    versoes = {}
    for commit in git("rev-list", "HEAD").split():
        for linha in git("ls-tree", "-r", commit).splitlines():
            meta, caminho = linha.split("\t", 1)
            _, tipo, sha = meta.split()
            if tipo == "blob" and caminho not in IGNORAR:
                versoes.setdefault(caminho, set()).add(sha)

    # O que esta no index (staged) tambem entra: e a versao que vai ser publicada neste commit.
    atual = []
    for linha in git("ls-files", "-s").splitlines():
        meta, caminho = linha.split("\t", 1)
        sha = meta.split()[1]
        if caminho in IGNORAR:
            continue
        versoes.setdefault(caminho, set()).add(sha)
        atual.append(caminho)

    manifesto = {
        "versao": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "atual": sorted(atual),
        "arquivos": {c: sorted(s) for c, s in sorted(versoes.items())},
    }
    SAIDA.write_text(json.dumps(manifesto, ensure_ascii=False, indent=1) + "\n")
    print(f"Manifesto gerado: {len(atual)} arquivos atuais, {len(versoes)} caminhos no historico.")


if __name__ == "__main__":
    main()
