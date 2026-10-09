---
name: onboarding
description: Onboarding e cadastro de cliente novo. Pergunta o nome, coleta site, Instagram e Google Meu Negócio, puxa as informações públicas (WebFetch → Firecrawl → fallback manual), cria a pasta do cliente, escreve o contexto.md e gera o estudo de persona e o estudo de mercado. Use quando o usuário disser "onboarding", "novo cliente", "cadastrar cliente", "adicionar cliente", "criar cliente", "entrou um cliente", "fazer onboarding do cliente X", "montar a pasta do cliente", ou rodar /onboarding. Também funciona só com um briefing colado, sem site nem redes.
---

# Onboarding de cliente novo

Estrutura o início do trabalho com um cliente. Coleta as fontes públicas dele (site, Instagram, Google Meu Negócio), extrai o máximo de informação, monta a pasta e produz três arquivos iniciais:

1. **`contexto.md`**: quem é o cliente, o que vende, contato, oferta, diferenciais, reputação
2. **`estudos/persona.md`**: estudo de persona profundo (skill `estudo-persona`)
3. **`estudos/mercado.md`**: estudo de mercado do segmento (skill `estudo-mercado`)

É o ponto de partida. Depois se refina com o que aprender na operação.

É a única porta de entrada de cliente novo no kit. Se o usuário só tiver um briefing (sem site, Instagram ou ficha do Google), seguir com o briefing: pular o Passo 2 e montar o contexto e os estudos com o que ele passou, deixando claro que ficaram mais inferidos.

---

## Regra 1 — Comece pelo nome

**SEMPRE** comece perguntando:

> "Qual é o nome do cliente que vamos fazer o onboarding?"

Não prossiga sem essa resposta. A partir do nome, defina um `slug` (minúsculo, sem espaço nem acento, ex: `clinica-sorriso-reto`).

Se `clientes/<slug>/` já existir, **não recriar do zero**: ler os arquivos que já estão lá, atualizar com as fontes novas e marcar no topo de cada arquivo a data e o que mudou.

---

## Passo 1 — Coletar as fontes

Pedir ao usuário, em bloco:

> Pra puxar as informações do cliente, me passa o que tiver (pode deixar em branco o que não houver):
>
> 1. **Site**: URL (ex: `https://cliente.com.br`)
> 2. **Instagram**: @ ou link do perfil
> 3. **Google Meu Negócio**: link da ficha no Google Maps (ou nome + cidade pra eu localizar)
> 4. **Briefing / material extra**: anotações da reunião, áudio transcrito, catálogo, página de vendas, ticket, verba, objetivo
> 5. **Logo** (opcional): se tiver, salva em `clientes/<slug>/marca/`

Se faltar alguma fonte, seguir só com as que houver.

---

## Passo 2 — Puxar as informações (cadeia de fallback)

Para **cada** fonte, tentar nesta ordem e anotar o que deu certo:

1. **WebFetch**: primeira tentativa pra site. Funciona bem em site institucional.
2. **Firecrawl**: se o WebFetch falhar, vier vazio ou bloqueado. `firecrawl_scrape` pra uma página, `firecrawl_search` pra achar a ficha do Google pelo nome + cidade.
   - **Link `share.google/...`**: o Firecrawl não abre direto. Seguir o redirect com `curl -sIL <link>` e usar a URL final, ou fazer `firecrawl_scrape` em `https://www.google.com/maps/search/<Nome>+<cidade>?hl=pt-BR` com `proxy: stealth` e `location: BR`.
   - Na ficha, registrar se aparece **"Reivindicar esta empresa"** (ficha sem dono). Isso muda a prioridade de tudo.
3. **Fallback manual**: se as duas falharem, **avisar claramente** qual fonte não abriu e pedir pro usuário colar na mão (bio do Instagram, descrição da ficha, textos do site).

**Instagram:** WebFetch e Firecrawl costumam bater no muro de login. Se existir `SCRAPECREATORS_API_KEY` no `.env` da raiz, usar a API (`GET https://api.scrapecreators.com/v1/instagram/profile?handle=<handle>` com header `x-api-key`): traz bio, link, seguidores, categoria e os últimos posts com legenda e curtidas. Sem a chave, tentar Firecrawl uma vez e, se bloquear, pedir a bio e os temas dos posts ao usuário.

> **Sempre dizer o que conseguiu e o que não conseguiu.** Ex: "Consegui o site e a ficha do Google. O Instagram bloqueou (muro de login). Me cola a bio e os destaques, por favor."

O que extrair de cada fonte:
- **Site:** produtos/serviços, proposta de valor, público aparente, tom de voz, provas (depoimentos, números), contato, região de atuação.
- **Instagram:** bio, link da bio, temas dos posts, como fala com a audiência, frequência, formatos, engajamento (vídeo x imagem).
- **Google Meu Negócio:** categoria, endereço, horário, nota e volume de avaliações, elogios e reclamações recorrentes nas reviews. As reviews são a melhor fonte de dor e desejo da persona: ler as de texto, não só a nota.

---

## Passo 3 — Criar a pasta e o contexto

Estrutura:

```
clientes/<slug>/
├── contexto.md
└── estudos/
    ├── persona.md
    └── mercado.md
```

Escrever `clientes/<slug>/contexto.md` usando `clientes/_template/contexto.md` como base. Preencher com o que foi levantado no Passo 2 e com o briefing do usuário.

- **Só dado confirmado.** Preço, contato, endereço, horário e oferta entram só se vieram de uma fonte ou do usuário.
- O que não deu pra confirmar vai na seção **Lacunas**. Nunca inventar.
- Registrar em **Fontes** o link de cada fonte e se foi acessada ou não.

---

## Passo 4 — Confirmar o nicho

Antes dos estudos, declarar o nicho e confirmar com o usuário:

> "Pelo que levantei, o nicho do cliente é **[nicho]**, atendendo **[região]**. Vou montar a persona e o mercado em cima disso. Confere?"

Não rodar os estudos sem o nicho confirmado.

---

## Passo 5 — Estudo de persona

Seguir a skill `estudo-persona` (`.claude/skills/estudo-persona/SKILL.md`) com o que já foi levantado. Não precisa refazer a coleta nem reconfirmar o nicho. Salvar em `clientes/<slug>/estudos/persona.md`.

---

## Passo 6 — Estudo de mercado

Seguir a skill `estudo-mercado` (`.claude/skills/estudo-mercado/SKILL.md`). Salvar em `clientes/<slug>/estudos/mercado.md`.

---

## Passo 7 — Fechar e reportar

Mostrar o resumo:

```
Onboarding de <Nome do Cliente> concluído

clientes/<slug>/
├── contexto.md         (dados do cliente, fontes, reputação, lacunas)
├── estudos/persona.md  (persona + aprofundamento + níveis de consciência)
└── estudos/mercado.md  (panorama, concorrência, posicionamento, canais)

Fontes acessadas:  <site / Instagram / Google: o que entrou>
Fontes pendentes:  <o que não abriu e precisa do usuário>
Ficha do Google:   nota <N> com <N> avaliações, reivindicada: sim/não
```

Listar as lacunas importantes (fonte bloqueada, preço ou oferta não confirmados, ficha sem dono) e pedir pra completar.

Depois sugerir os próximos passos que fizerem sentido pro cliente, por exemplo:
- `/setup-rastreamento-cliente-gtm-ga4` se ele ainda não tem GA4, GTM e conversões
- `/proposta-comercial` se ainda está em fase de proposta
- 10 roteiros de anúncio a partir da persona, se o usuário quiser (salvar em `clientes/<slug>/criativos/roteiros-anuncios.md`: título, persona e nível de consciência, formato, gancho de 0 a 3 s, desenvolvimento, virada, CTA, legenda sem emoji; respeitando as lacunas)

---

## Regras

- **Nome primeiro, sempre.** Sem nome, não prossiga.
- **Nicho confirmado antes dos estudos.**
- **Cadeia de fallback obrigatória** (WebFetch → Firecrawl → usuário) e **sempre avisar** o que não abriu. Nunca fingir que acessou.
- **Não inventar dado factual do cliente.** Persona e mercado podem ser inferidos (é o trabalho), mas preço, contato, endereço e oferta só entram confirmados.
- **Calibrar com o real.** Reviews do Google e temas do Instagram alimentam a persona de verdade. Persona genérica não serve.
- **Tudo na pasta do cliente.** É o que as outras skills (campanhas, criativos, propostas) vão ler depois.
- **Tom e estilo:** seguir `_contexto/preferencias.md`. Português, sem emoji no que for entregue ao cliente.
