---
name: atualizar-kit
description: Atualiza o kit ClaudePRO com as novidades do repositório oficial sem sobrescrever nada do usuário. Baixa a versão nova, adiciona skills e arquivos novos, atualiza só o que o usuário nunca editou, nunca toca em contexto, marca, clientes, dados e credenciais, e mescla com aprovação os arquivos que o usuário personalizou. Use quando o usuário disser "atualizar o kit", "tem novidade no ClaudePRO?", "puxar as atualizações", "atualizar as skills", "baixar a versão nova", ou rodar /atualizar-kit. Não confundir com /atualizar, que revisa os arquivos de contexto.
---

# Atualizar o kit ClaudePRO

O script `.kit/atualizar.py` baixa a versão oficial do GitHub e compara arquivo por arquivo com o que o
usuário tem. Ele sabe se o usuário mexeu num arquivo porque o `.kit/manifesto.json` guarda a impressão
digital de todas as versões oficiais que já existiram de cada arquivo.

| Situação | O que acontece |
|---|---|
| Arquivo novo no kit | É adicionado |
| Arquivo que o usuário nunca editou | É substituído pela versão nova (com backup) |
| Arquivo que o usuário editou | **Não é tocado.** A versão nova vai pra `.kit/revisar/` e você mescla com ele |
| Arquivo que o usuário editou e o kit não mudou desde a última mesclagem | Fica quieto |
| `_contexto/`, `marca/`, `clientes/` (menos `_template`), `dados/`, `.env`, `contas.yaml` | Nunca é tocado |
| Caminhos em `.kit/protegidos-locais.txt` | Nunca é tocado |
| Arquivo do kit que o usuário apagou | Continua apagado |
| Arquivo que saiu do kit oficial | Fica, só é avisado |

Nada é apagado. Tudo que é substituído vai antes pra `.kit/backup/<data>/`.

---

## Passo 1 — Simular

Rodar (no Windows, se `python3` não existir, usar `python` ou `py`):

```bash
python3 .kit/atualizar.py --json
```

Se o `.kit/atualizar.py` não existir (kit baixado antes do atualizador), buscar ele primeiro:

```bash
mkdir -p .kit && curl -fsSL https://raw.githubusercontent.com/cassiorox/ClaudePRO/main/.kit/atualizar.py -o .kit/atualizar.py
```

Se der erro de download (sem internet, repositório privado), avisar e parar.

## Passo 2 — Explicar em linguagem simples

Ler `NOVIDADES.md` da versão nova (está na lista de `novo` ou `atualizar`; ler em
`https://raw.githubusercontent.com/cassiorox/ClaudePRO/main/NOVIDADES.md` se precisar) e mostrar o que
mudou desde a versão local. Depois o plano, agrupado, sem listar centenas de arquivos:

> "Tem novidade no kit (versão de <data>):
> - <2 a 4 novidades principais do NOVIDADES.md>
>
> O que vai acontecer:
> - N arquivos novos (ex: skills `x` e `y`)
> - N arquivos atualizados (você nunca mexeu neles)
> - N arquivos que você personalizou e eu vou mesclar com você: `AGENTS.md`, ...
> - Teu contexto, marca, clientes e credenciais não são tocados.
>
> Posso aplicar?"

Se não houver nada em `novo`, `atualizar` nem `revisar`: "Teu kit já está na versão mais nova." e parar.

Se a pasta for um repositório Git com mudanças não commitadas, sugerir um commit antes ("ponto de
restauração"). Não é obrigatório: o backup do script já protege.

## Passo 3 — Aplicar

Com o ok do usuário:

```bash
python3 .kit/atualizar.py --aplicar --json
```

## Passo 4 — Mesclar os arquivos personalizados

Para cada arquivo em `revisar`, comparar a versão do usuário (`<caminho>`) com a oficial
(`.kit/revisar/<caminho>`). Se existir `.kit/base/<caminho>` (a versão oficial da última mesclagem),
o `diff` entre `.kit/base/<caminho>` e `.kit/revisar/<caminho>` mostra exatamente o que o kit mudou
desde então: usar isso como guia.

1. Identificar o que o kit mudou (seções novas, instruções corrigidas, passos novos) e o que o usuário
   personalizou (regras que ele adicionou, textos que ele adaptou ao negócio dele).
2. Propor a mesclagem: **tudo que o usuário escreveu fica**, e as melhorias do kit entram. Se uma
   mudança do kit contradiz algo que o usuário personalizou, a versão do usuário vence e você avisa.
3. Mostrar um resumo curto do que entra ("vai entrar a seção X e o passo Y; tuas 3 regras ficam") e pedir
   ok arquivo a arquivo. Se forem muitos arquivos, perguntar se pode aplicar todos de uma vez.
4. Com o ok, gravar o arquivo mesclado.
5. Se o usuário preferir não mesclar, deixar o arquivo dele como está.
6. **Nos dois casos**, mover a cópia de `.kit/revisar/<caminho>` para `.kit/base/<caminho>` (criando as
   pastas). É isso que faz a próxima atualização ficar quieta enquanto o kit não mudar esse arquivo de novo.

Casos comuns:
- **`AGENTS.md`**: manter todas as regras que o usuário adicionou (normalmente vindas de "Aprender com
  correções") e trazer as seções novas do kit.
- **`aprendizados.md` das skills**: juntar as duas listas de regras, sem duplicar.
- **`SKILL.md` editado pelo usuário**: trazer passos novos e correções, sem desfazer a adaptação dele.

## Passo 5 — Fechar

```
Kit atualizado para a versão <data>

Novos:        N (ex: skills onboarding, estudo-persona)
Atualizados:  N
Mesclados:    N (AGENTS.md, ...)
Intocados:    contexto, marca, clientes, dados, credenciais
Backup:       .kit/backup/<data>/
```

Se apareceu algo em `removido`, listar e perguntar se quer apagar. Se apareceram skills novas,
dizer em uma linha pra que serve cada uma.

---

## Regras

- **Sempre simular antes de aplicar** e só aplicar com o ok do usuário.
- **Nunca sobrescrever arquivo em `revisar`** sem mostrar a mesclagem e ter o ok.
- **Nunca editar** `_contexto/`, `marca/`, `clientes/` ou credenciais durante a atualização.
- **Proteger algo a mais:** se o usuário quiser que um arquivo nunca seja atualizado (ex: uma skill do kit
  que ele reescreveu toda), adicionar o caminho em `.kit/protegidos-locais.txt` (um por linha, aceita
  `pasta/**`).
