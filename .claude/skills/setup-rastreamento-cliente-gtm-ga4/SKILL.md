---
name: setup-rastreamento-cliente-gtm-ga4
description: Monta do zero o rastreamento de um cliente novo, via API — conta GA4 no nome do cliente (propriedade, fluxo, retenção 14 meses, evento-chave, vínculo com Ads), conversões no Google Ads (lead principal, chamada, WhatsApp e rotas), container GTM completo (GA4, Conversion Linker, conversões otimizadas com telefone, WhatsApp em 3 camadas), prompt do site (Lovable ou similar) com o evento lead_form, validação em 4 camadas e publicação. Use quando o usuário disser "rastreamento do cliente X", "criar GA4 e GTM", "configurar Analytics, Tag Manager e conversões", "setup de conversões pro Google Ads", "cliente novo, cria o Analytics", ou rodar /setup-rastreamento-cliente-gtm-ga4.
---

# Setup de rastreamento do cliente: GA4 + Google Ads + GTM

Monta o rastreamento inteiro de um cliente novo, passo a passo, com o usuário só fazendo os cliques que o Google exige de um humano.

Scripts em `scripts/` (python3 do sistema, sem venv). `ads_conversions.py` usa o SDK da skill `google-ads`. Todos **nunca imprimem token**. Os comandos abaixo rodam de dentro da pasta da skill (`.claude/skills/setup-rastreamento-cliente-gtm-ga4/`).

## Credenciais

- `GOOGLE_ADS_CLIENT_ID` e `GOOGLE_ADS_CLIENT_SECRET`: reaproveitados do `.env` da skill `google-ads`. Se ainda não existir, rodar `/google-ads setup` antes.
- `GA4_REFRESH_TOKEN` e `GTM_REFRESH_TOKEN`: gerados na Etapa 0 e gravados no `.env` **desta skill** (no `.gitignore`; modelo em `.env.example`).
- Nunca colar token no chat, em `clientes/` ou em qualquer arquivo versionado.

## Regras

- Uma etapa por vez. Ao fim de cada etapa: mostrar o que foi criado (tabela com IDs) e pedir OK antes da próxima quando ela criar algo na conta do cliente.
- Contas GA4 e GTM ficam **no nome do cliente**, com a agência/gestor como administrador (perguntar só se o usuário não disser).
- Criar no GTM sempre num **workspace novo**; publicar só depois da validação (etapa 5).
- Registrar tudo em `clientes/<slug>/rastreamento.md` (IDs + checklist das etapas), atualizando a cada etapa. Se o cliente não tiver pasta, sugerir `/onboarding` antes.
- Usar a Tag Manager API direta. Evitar MCPs de terceiros com cota diária compartilhada (estouram com 429 "per day" no meio do build).

## Entradas (perguntar o que faltar)

1. Nome do cliente e slug da pasta em `clientes/` (ler `clientes/<slug>/contexto.md`)
2. URL do site e onde ele é editado (Lovable, WordPress, código)
3. Customer ID do Google Ads (conta já criada)
4. O que é conversão principal (padrão: formulário que leva ao WhatsApp + chamada pelo anúncio) e se há botão "Como chegar"
5. Categoria do negócio no GA4 (`--category`, ex.: `HEALTHCARE`, `BUSINESS_AND_INDUSTRIAL_MARKETS`, `OTHER`)
6. Ler o plano de campanhas/conversões e o prompt-base do site do cliente, se existirem, para herdar nomes de evento e de chave

## Etapa 0: tokens (uma vez por máquina/login)

Checar escopos: `python3 -c "import sys; sys.path.insert(0,'scripts'); from _google import access_token as a; print(a('GA4_REFRESH_TOKEN')[1]); print(a('GTM_REFRESH_TOKEN')[1])"`

- Falta `analytics.edit` ou `GA4_REFRESH_TOKEN` → `python3 scripts/oauth_login.py ga4` (em background; mandar o link ao usuário; se der "400 That's an error", janela anônima).
- Falta `GTM_REFRESH_TOKEN` → `python3 scripts/oauth_login.py gtm`.
- Antes, no projeto do Google Cloud que gerou o Client ID, ativar a **Google Analytics Admin API**, a **Google Analytics Data API** e a **Tag Manager API** (console.cloud.google.com → APIs e serviços → Biblioteca). 403 "has not been used" = não ativada ou propagando; tentar de novo em 1 min.
- O login do OAuth usa `http://127.0.0.1:8765/` como retorno. O Client ID precisa ser do tipo "App para computador" (o mesmo da skill `google-ads` já é).

## Etapa 1: GA4

1. `python3 scripts/ga4_setup.py list` → confirmar que o cliente ainda não tem conta.
2. `python3 scripts/ga4_setup.py ticket --name "<Nome do Cliente>"` **em background**. Mandar o link de termos ao usuário. Quando ele aceitar, a saída mostra `CONTA CRIADA: accountId = N`.
3. `python3 scripts/ga4_setup.py setup --account N --property-name "<Cliente> - Site" --site https://... --ads <customer> --category <CATEGORIA>` → propriedade, fluxo web (`G-...`), retenção 14 meses, evento-chave `lead_form`, vínculo com o Ads.

## Etapa 2: Google Ads

`python3 scripts/ads_conversions.py create --customer <id>` (opções `--sem-maps`, `--sem-chamada`, `--call-seconds 60`). Imprime a tabela com o `send_to` (`AW-<id>/<rótulo>`) de cada uma. Guardar os rótulos para a etapa 3.

- O vínculo da etapa 1 importa eventos-chave do GA4 como ações **ocultas** no Ads. Manter ocultas: ativar a `lead_form` importada duplica o lead.
- Conversões otimizadas para leads: só pela interface (Metas → Configurações → Conversões otimizadas para leads → método Google Tag Manager → aceitar termos de dados do cliente). Pedir ao usuário.

## Etapa 3: GTM

1. O usuário cria a **conta** do GTM na interface (tagmanager.google.com → Criar conta, container Web com o domínio), com o mesmo login usado no `GTM_REFRESH_TOKEN`. Nenhuma API cria conta. Pedir o `GTM-XXXX` e, se possível, o número da conta (evita varrer todas e bater no limite por minuto).
2. `python3 scripts/gtm_build.py find --public-id GTM-XXXX [--account-id N]`
3. `python3 scripts/gtm_build.py build --public-id GTM-XXXX --account-id N --ga4 G-... --aw <digitos> --label-lead ... --label-wpp ... [--label-maps ...] [--exclude-text "Abrir WhatsApp"]`

Cria: 19 variáveis integradas; `CONST - GA4 Measurement ID`, `CONST - AW Conversion ID`, `DLV - telefone/pagina/convenio`, `UPD - Lead (telefone)` (awec manual); acionadores `CE - lead_form`, WhatsApp em 3 camadas (link `wa.me`, botão sem link com texto "whatsapp" que não é link de WhatsApp nem o botão de reserva, evento `whatsapp_click`), `Click - Como chegar`; tags Google Tag GA4 + Conversion Linker (All Pages), GA4 e Ads para lead (com conversões otimizadas), WhatsApp e rotas. Termina com `compilerError: None`.

Se o site usa outros nomes de chave no dataLayer (ex.: `servico` no lugar de `convenio`), ajustar as variáveis `DLV - *` depois do build (GET + PUT com o fingerprint).

## Etapa 4: site

Preencher `references/prompt-site.md` (GTM ID, WhatsApp, nomes de chave) e salvar em `clientes/<slug>/landing/prompt-lovable-rastreamento.md`. O usuário cola no Lovable (ou passa pra quem edita o site) e publica.

## Etapa 5: validação e publicação

1. **Código do site:** `python3 scripts/check_site.py https://site GTM-XXXX` → snippet no head e noscript no body, nada de gtag direto, `lead_form` com `eventCallback`, links `wa.me`/Maps. Se aparecer botão de WhatsApp sem link que só existe depois do formulário, garantir que o `--exclude-text` cobre o texto dele.
2. **Publicar:** `python3 scripts/gtm_build.py publish --workspace <path> --name "v1 - Setup inicial GA4 + Google Ads" --notes "..."` (o container vazio já carregava no site; publicar não quebra nada).
3. **Navegador automatizado** (se houver um disponível, ex.: skill `agent-browser` ou Claude in Chrome): abrir o site com `?utm_source=teste-ia&utm_medium=qa`, conferir `google_tag_manager` com o GTM e o `G-`, clicar nos links de WhatsApp e Maps com `preventDefault` via `eval` e ler `dataLayer` (`gtm.linkClick` com os triggers) e `performance.getEntriesByType('resource')` (`g/collect` e `googleadservices.com/pagead/conversion/<AW>`). Sem navegador automatizado, pedir ao usuário para testar no modo Preview do GTM.
4. **Tempo real:** `python3 scripts/realtime.py --property <id> --need page_view lead_form`. O envio do formulário é feito **pelo usuário** (um teste da IA cai no painel de leads do cliente).
5. **Ads:** conferir `customer.conversion_tracking_setting.enhanced_conversions_for_leads_enabled` e `accepted_customer_data_terms` = true (consulta GAQL pela skill `google-ads`, resource `customer`).
6. Conferir `python3 scripts/ga4_setup.py status --property <id>`: medição otimizada ligada (com `pageChangesEnabled`, obrigatório em site React/SPA).

Cliques podem demorar a aparecer no tempo real mesmo com a requisição enviada: conferir nos relatórios padrão em até 24h antes de fechar.

## Orientações ao usuário (configurações só na interface)

- GA4 > Coleta de dados: ligar Indicadores do Google e confirmar a coleta de dados fornecidos pelo usuário.
- GA4 > Exibição de dados > Identidade do relatório: **baseado no dispositivo** em conta de pouco tráfego (Combinada/Observada com Indicadores ligados aplicam limite de dados e escondem linhas). Só muda a exibição, dá pra trocar depois.
- Medição otimizada: manter ligada.

## Saída final

Tabela de IDs (conta/propriedade/G-, customer/AW-, conta/container/GTM-, versão publicada), checklist das 5 etapas com o que ficou pendente, e `clientes/<slug>/rastreamento.md` atualizado.

---

*Criada por Cássio Prado.*
