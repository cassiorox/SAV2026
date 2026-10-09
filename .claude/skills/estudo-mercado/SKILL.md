---
name: estudo-mercado
description: Gera o estudo de mercado do segmento de um cliente, calibrado pela cidade e região. Cobre panorama e tendências, concorrentes diretos e indiretos (com o que anunciam na Biblioteca de Anúncios da Meta), posicionamento do cliente, demanda de busca no Google, comportamento de compra, canais, riscos do nicho e próximos passos. Salva em clientes/<slug>/estudos/mercado.md. Use quando o usuário pedir "estudo de mercado", "análise de concorrentes", "concorrência do cliente X", "como está o mercado de X", "benchmark", ou rodar /estudo-mercado. Também é chamada pela skill onboarding.
---

# Estudo de mercado

Mapeia o mercado em que o cliente joga, pra decidir posicionamento, oferta e onde anunciar.

---

## Antes de começar

1. **Qual cliente?** Ler `clientes/<slug>/contexto.md` e `estudos/persona.md` se existir.
   - Sem pasta: sugerir `/onboarding` antes.
2. **Nicho e região confirmados.** "Vou estudar o mercado de **[nicho]** em **[cidade/região]**. Confere?" (Pular se veio do `onboarding`.) Mercado local e mercado nacional/digital são estudos diferentes. Deixar claro qual é.
3. **Concorrentes conhecidos.** Perguntar se o usuário ou o cliente já sabe quem são os concorrentes. Somar com o que a pesquisa achar.

---

## Pesquisa (usar dado real, não só conhecimento geral)

Ir atrás de fonte externa. Registrar a fonte de cada dado relevante.

- **Concorrentes:** `firecrawl_search` (ou WebSearch) por "<nicho> em <cidade>", "melhor <nicho> <cidade>" e no Google Maps. De cada concorrente, olhar site, Instagram e ficha do Google (nota, volume de avaliações, o que elogiam e o que reclamam).
- **O que os concorrentes anunciam:** Biblioteca de Anúncios da Meta. Se o conector Meta Ads estiver disponível, usar `ads_library_search` pelo nome ou pela página do concorrente. Senão, `firecrawl_scrape` em `https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=BR&q=<nome>`. Anotar: há quanto tempo o anúncio roda (anúncio antigo ativo é sinal de que dá resultado), formato, oferta, promessa, CTA.
- **Demanda de busca:** se a skill `google-ads` estiver configurada, rodar o Keyword Planner (`.claude/skills/google-ads/scripts/keyword_planner.py`) com as palavras do nicho e a localização do cliente. Volume mensal, CPC estimado e concorrência. Sem acesso, usar o Google Trends ou deixar como lacuna.
- **Tendências e números do setor:** dados de associação do setor, IBGE, notícias recentes. Sempre com fonte e data.
- **Regras do nicho:** políticas de anúncio da Meta e do Google pra categorias sensíveis (saúde, estética, finanças, imóveis, emprego, bebida, jogos) e regras do conselho profissional (CFM, CFO, OAB, CRMV etc.) quando houver.

Se uma fonte não abrir, dizer qual e seguir.

---

## Estrutura (salvar em `clientes/<slug>/estudos/mercado.md`)

```markdown
# Estudo de Mercado — <Nome do Cliente>

Segmento, região, data do levantamento e fontes usadas.

## 1. Panorama do segmento
- O que é o mercado, tamanho/relevância na região, tendências e pra onde caminha.

## 2. Concorrência
Tabela com os principais concorrentes (diretos e indiretos):
| Concorrente | Onde | Promessa / posicionamento | Preço (se público) | Nota Google | Anuncia? | Ponto forte | Ponto fraco |

## 3. O que os concorrentes anunciam
- Anúncios ativos de cada um: formato, oferta, promessa, CTA, há quanto tempo roda.
- Padrões do nicho (o que todo mundo faz) e o que ninguém está fazendo.

## 4. Posicionamento do cliente
- Onde o cliente está hoje vs. a concorrência.
- Diferenciais reais e percebidos.
- Lacunas e oportunidades de posicionamento.

## 5. Demanda e comportamento de compra
- Volume de busca das principais palavras, CPC estimado (se levantado).
- Como esse público pesquisa e decide. Sazonalidade, gatilhos de compra, objeções típicas.

## 6. Canais e oportunidades
- Onde esse público está (Meta, Google Search, Google Maps, orgânico, indicação, marketplace).
- As oportunidades de aquisição mais promissoras pra este cliente, em ordem.

## 7. Riscos e atenção
- Restrições de política de anúncio, regulação, sazonalidade, dependência de canal.

## 8. Conclusão e próximos passos
- Resumo do que o mercado pede e por onde começar (3 a 5 ações concretas).
```

---

## Regras

- **Dado com fonte.** Número sem fonte vira estimativa e é marcado como tal.
- **Não inventar concorrente nem preço.** Se não achou, escrever que não achou.
- **Calibrar pela região.** Benchmark nacional só entra como referência, marcado.
- **Conectar com a persona** quando `estudos/persona.md` existir: as objeções e gatilhos da seção 5 têm que bater com ela.
- Se o arquivo já existia, atualizar e registrar no topo a data e o que mudou.

## Fechar

Mostrar onde salvou e um resumo de 3 linhas: quem domina o mercado, a maior brecha encontrada e o primeiro passo recomendado. Listar o que ficou sem fonte.
