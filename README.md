# ClaudePRO — Kit de Boas-Vindas

Framework **ClaudePRO** pra usar o Claude Code com contexto do seu negócio.

---

## Como instalar

**1. Copie o repositório**

Escolha uma das opções:

- **Opção A (recomendada):** clique em **"Use this template" → "Create a new repository"** no topo desta página do GitHub. Isso cria uma cópia sua, sem nenhum vínculo com este repositório. Depois clone a **sua** cópia.

- **Opção B:** clone direto e desvincule do repositório original:
```bash
git clone https://github.com/cassiorox/ClaudePRO.git
cd ClaudePRO
git remote remove origin
```

> **Importante:** o `git remote remove origin` garante que nada do que você salvar aqui (contexto do negócio, clientes, credenciais) fique apontando pro repositório público. Se esquecer, sem problema — o `/setup` faz isso automaticamente.

**2. Abra no VS Code**
```bash
code .
```

**3. Abra o terminal integrado** (Ctrl + ` no Windows / Cmd + ` no Mac) e rode:
```bash
claude
```

**4. Chame o setup**
```
/setup
```

---

O Claude vai te fazer algumas perguntas e configurar o sistema pro seu negócio. Em 5 minutos você tem tudo pronto.

---

## O que vem no kit

**Skills prontas pra usar:**
- `/setup` — configura o sistema pro seu negócio (comece por aqui)
- `/onboarding` — cadastro e onboarding de cliente novo: puxa site, Instagram e Google Meu Negócio, cria a pasta, o contexto.md e gera os estudos de persona e de mercado
- `/estudo-persona` — estudo de persona profundo (medos, dores, objeções, níveis de consciência), calibrado pelas reviews e redes do cliente
- `/estudo-mercado` — estudo de mercado do segmento: concorrentes, o que eles anunciam na Biblioteca de Anúncios, demanda de busca, canais e riscos
- `/meta-ads` — gerencia campanhas Meta Ads (Facebook/Instagram) via SDK oficial
- `/google-ads` — gerencia campanhas Google Ads via SDK oficial
- `/auditoria-conta-google-ads` — audita uma conta Google Ads inteira, mostra onde o dinheiro vaza e entrega um plano de correção em fases
- `/setup-rastreamento-cliente-gtm-ga4` — monta o rastreamento de um cliente novo via API: GA4, conversões no Google Ads, container GTM completo, prompt do site e validação
- `/proposta-comercial` — cria propostas comerciais em PDF com a identidade visual da sua marca
- `/atualizar-kit` — traz as novidades do kit sem sobrescrever o que é teu (ver abaixo)

**Skills de terceiros (créditos em `CREDITOS.md`):**
- `/meta-vv-publicos` — cria públicos de video view na Meta Ads por retenção, a partir dos vídeos orgânicos do Instagram ou dos anúncios de uma campanha. Por [Igor Poggianella](https://github.com/igorpoggianella/meta-vv-publicos)
- `/bro` — reexplica a última resposta do Claude em linguagem simples. Por [Luka (luchasarie)](https://github.com/luchasarie/bro-skill)
- `/eli5` — explica qualquer assunto "como se eu tivesse 5 anos", com imagens grandes e poucas palavras. Por [Thariq Shihipar (Anthropic)](https://github.com/anthropics/claude-plugins-community/tree/main/eli5)

**Instruções do workspace:**
- `AGENTS.md` — o arquivo real de instruções, lido por Claude Code, Codex, Cursor, Gemini CLI e outros agentes. É aqui que entra toda regra nova
- `CLAUDE.md` — só um ponteiro (`@AGENTS.md`) mais o que for exclusivo do Claude Code. Não escreva instrução nova aqui

**Materiais de apoio:**
- `.claude/skills/google-ads/references/mcp-server.md` — playbook do servidor MCP oficial do Google Ads (leitura direta da conta dentro do Claude), incluindo por que no Meta o conector é de um clique e no Google não

**Pastas geradas pelo `/setup`:**
- `_contexto/` — contexto do seu negócio e preferências
- `marca/` — guia de identidade visual da sua marca
- `templates/ferramentas/catalogo.md` — APIs, CLIs e MCPs disponíveis pra usar em skills

**Pasta `dados/`:**
- Drop zone pra arquivos que você quer analisar (CSV, XLSX, TXT, PDF)
- Útil quando você não tem MCP de Google Drive instalado

---

## Como atualizar o kit

Quando sair novidade (veja `NOVIDADES.md`), rode `/atualizar-kit` dentro do Claude Code. Ele:

- adiciona as skills e arquivos novos;
- atualiza só os arquivos que você nunca editou (com backup em `.kit/backup/`);
- **nunca toca** em `_contexto/`, `marca/`, `clientes/`, `dados/` e credenciais;
- nos arquivos que você personalizou (ex: `AGENTS.md`), mostra o que mudou e mescla com você, mantendo tudo que é teu.

Não precisa de Git nem de `git pull`. Funciona mesmo se você baixou o ZIP ou usou "Use this template".
Pra blindar um arquivo específico contra atualização, coloque o caminho em `.kit/protegidos-locais.txt`.

