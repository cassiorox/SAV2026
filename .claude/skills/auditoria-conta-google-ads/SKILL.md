---
name: auditoria-conta-google-ads
description: Audita uma conta Google Ads inteira pra achar onde o dinheiro vaza e entregar um plano de correcao em fases. Cobre segmentacao por presenca x interesse, tipos de correspondencia, termos de pesquisa, marca misturada com generico, estrategia de lance sem teto, acoes e metas de conversao, dispositivo, parcela de impressao perdida por classificacao x orcamento, demanda real no Keyword Planner, velocidade e alinhamento da pagina de destino. Nao altera nada sem aprovacao. Use quando o usuario pedir "auditar conta do google ads", "por que minha campanha nao gera lead", "revisar conta antes de aumentar verba", "onde estou perdendo dinheiro no google", "diagnostico da conta", ou rodar /auditoria-conta-google-ads.
---

# Auditoria de conta Google Ads

Diagnóstico completo de uma conta que gasta e não entrega. Só leitura. Nada é alterado sem aprovação explícita.

O produto final é um relatório com três partes: onde o dinheiro vaza (com o valor em reais de cada vazamento), o que está certo e não precisa mexer, e um plano em fases que começa hoje.

## Princípio central

Três coisas precisam bater: **busca da pessoa → serviço que o negócio realmente vende → conteúdo da página de destino**.

Quando uma delas não bate, o resultado é verba queimada, índice de qualidade baixo e lead desqualificado. E a auditoria não termina no diagnóstico: termina num plano que cabe numa manhã.

## Passo 0 — Definir o acesso e o contexto

Antes de qualquer coisa, perguntar ao usuário:

- Nome do negócio e o que ele vende.
- ID da conta (formato 000-000-0000).
- Site e a página para onde os anúncios levam.
- Cidade e região atendidas.
- O que conta como resultado: lead pelo formulário, mensagem no WhatsApp, venda no site, ligação.
- Ticket médio ou quanto vale um cliente novo.
- Período a analisar (padrão: últimos 12 a 13 meses).

Depois, identificar o acesso disponível, nesta ordem:

1. Skill `google-ads` deste kit (scripts em `.claude/skills/google-ads/scripts/`). É o caminho padrão.
2. MCP oficial do Google Ads, se estiver conectado.
3. Nenhum dos dois: pedir exportações da interface, indicando o caminho exato e o período. No mínimo: campanhas, grupos de anúncios, palavras-chave com índice de qualidade, termos de pesquisa, anúncios, recursos (extensões), conversões por ação, e os segmentos por dispositivo e por localização com a distinção entre presença e interesse.

Nunca inventar número. Dado que não existe vira "sem dado", e o relatório diz de onde veio cada número.

## Passo 1 — Puxar a conta inteira

Puxar tudo, inclusive campanhas pausadas e removidas. A campanha que o cliente cita raramente é a única que importa, e reestruturações prontas costumam estar paradas na conta (IDs mais altos são mais recentes).

Com a skill `google-ads`:

```bash
cd .claude/skills/google-ads/scripts
python3 read.py campaigns         --customer-id <CID>
python3 read.py ad-groups         --customer-id <CID> --campaign-id <ID>
python3 read.py keywords          --customer-id <CID> --campaign-id <ID>
python3 read.py ads               --customer-id <CID> --campaign-id <ID>
python3 read.py search-terms      --customer-id <CID>
python3 read.py negative-keywords --customer-id <CID>
python3 read.py quality-scores    --customer-id <CID>
python3 read.py extensions        --customer-id <CID>
python3 insights.py campaign      --customer-id <CID> --date-range LAST_30_DAYS
python3 insights.py device        --customer-id <CID> --date-range LAST_30_DAYS
python3 insights.py daily         --customer-id <CID> --since <data> --until <data>
```

O que os scripts prontos não cobrem e precisa de GAQL direto (ou da interface):

- Configuração de geo: `campaign.geo_target_type_setting.positive_geo_target_type` e os `campaign_criterion` de localização.
- Redes ativadas: `campaign.network_settings` (pesquisa, parceiros, display).
- Teto de CPC da estratégia: `campaign.target_spend.cpc_bid_ceiling_micros` ou `campaign.maximize_conversions`.
- Métricas por localização, separando presença de interesse: `geographic_view` com `geo_target_constant` e `location_type`, ou `user_location_view`.
- Parcela de impressões: `metrics.search_impression_share`, `search_rank_lost_impression_share`, `search_budget_lost_impression_share`.
- Ações de conversão: `conversion_action` com categoria, origem e `primary_for_goal`.
- Metas de conversão: `customer_conversion_goal` e `campaign_conversion_goal`, campo `biddable`.

## Passo 2 — Diagnóstico: onde o dinheiro vaza

Responder cada item com número do lado. Ordenar os achados pelo valor desperdiçado, do maior para o menor. Sem custo ao lado, não é achado, é opinião.

1. **Geografia.** A campanha está por presença ou por "presença ou interesse"? Quanto foi gasto com gente que só tem interesse na região? Apareceram cidades ou estados fora da área atendida? "Presença ou interesse" é o vazamento mais comum e o mais caro.
2. **Correspondência.** Quanto foi para correspondência ampla e o que ela puxou. Classificar os termos de pesquisa em: cliente real, quem quer aprender a fazer, quem procura emprego ou curso, nome de concorrente, plataforma em vez de serviço, fora da região.
3. **Palavras-chave que torram dinheiro.** As que mais gastaram sem gerar resultado, com custo, cliques, conversões e CPC. E qual gerou resultado, a que custo. Normalmente duas keywords concentram a maior parte do gasto.
4. **Marca misturada com genérico.** Se a marca divide grupo ou campanha com termos genéricos, comparar índice de qualidade e CPC dos dois. Marca barata com índice alto mascara genérico ruim na média.
5. **Lance e orçamento.** A estratégia tem teto de CPC? Com o orçamento atual, quantos cliques por dia a campanha consegue? Maximizar cliques sem teto em leilão caro gasta o dia em um ou dois cliques.
6. **Medição.** Quais ações de conversão existem e, principalmente, quais metas estão valendo para o lance. Rota no mapa, clique pra ligar, visita ao perfil e "engajamento" contando como conversão poluem o sinal. Identificar a ação que representa dinheiro, quando ela disparou pela última vez e se há período longo em zero, o que costuma ser rastreamento quebrado.
7. **Dispositivo.** Comparar celular e computador em custo, conversões e custo por conversão. Diferença grande costuma ter causa na velocidade da página no celular.
8. **Parcela de impressões, mês a mês.** Quanto se perde por classificação (qualidade e lance) e quanto por orçamento. Isso decide se o problema é verba ou qualidade. Cuidado: parcela que "melhora" pode significar apenas que sobrou a marca rodando, então olhar o volume de impressões junto.
9. **Anúncios.** Listar cada alegação dos títulos e descrições e dizer se ela existe no site. Anúncio que promete o que a página não entrega derruba a experiência da página e o índice de qualidade.
10. **Demanda real.** Levantar no Keyword Planner o volume na cidade, no estado e no país, com faixa de CPC. Concluir qual verba cobre a demanda local. Se o volume local for pequeno, dizer com todas as letras: mais verba não resolve, e o crescimento vem de outro canal.

## Passo 3 — Página de destino

Medir, não achar. Rodar no celular simulado:

```bash
npx -y lighthouse@12 "<URL>" --quiet --only-categories=performance,seo \
  --form-factor=mobile --output=json --output-path=lh.json --chrome-flags="--headless=new"
```

Relatar nota de performance, LCP, e qual elemento é o maior da primeira tela. Depois verificar:

- A palavra buscada aparece no título, no H1 e no primeiro parágrafo?
- O HTML inicial já traz o conteúdo, ou a página só aparece depois do JavaScript? Testar com `curl -s <URL> | grep -o '<h1[^>]*>[^<]*'`. Página de aplicação de página única costuma devolver o H1 e o título da home em todas as rotas, o que o Google lê como páginas iguais.
- Quantos cliques até o contato, quais canais, e se telefone e WhatsApp da página são reais.
- O evento de conversão dispara no envio do formulário? Existe página de obrigado?
- URL inexistente devolve 404 ou devolve a home com status 200?
- Cache do HTML e dos arquivos com hash no nome.

Se os anúncios apontam todos para a home existindo páginas por serviço, esse é quase sempre um dos três maiores achados.

## Passo 4 — Entregar

Ordem do relatório:

1. Um parágrafo de abertura em linguagem de dono de negócio, com os dois ou três números que explicam tudo.
2. Números da conta e tabela das campanhas com veredito por campanha (reestruturar, deixar pausada, ignorar, aposentar).
3. Os achados em ordem de dinheiro, cada um com o valor desperdiçado.
4. Onde o dinheiro foi: custo por keyword e os termos de pesquisa que não deviam ter sido pagos.
5. Demanda real e o que ela muda no plano.
6. Página de destino: o que já está certo e o que derruba o índice de qualidade.
7. Plano de ação em fases.
8. Copy pronta para colar, com pelo menos 12 títulos por grupo de anúncio.
9. Método e limites: o que não deu para ver e onde conferir na interface.

O plano sempre em quatro fases:

- **Fase 0, hoje, 30 minutos.** Mudanças cirúrgicas na campanha que está no ar, sem depender de nada novo: geografia, pausa das keywords ruins, teto de CPC, orçamento, limpeza das metas de conversão, teste da tag de conversão.
- **Fase 1, semana 1.** Estrutura nova com marca separada de captação. Tabela com campanha, grupo, keywords com tipo de correspondência, página de destino, orçamento e lance, mais a lista de negativas agrupada por motivo.
- **Fase 2, semanas 1 e 2.** Página de destino e velocidade, com um prompt pronto para colar em quem mexe no site.
- **Fase 3, meses 1 a 3.** Rotina semanal de 15 minutos e metas de 90 dias com número: CPC médio, custo por resultado, perda de impressão por classificação.

Fechar com o orçamento mensal recomendado por campanha e o total, comparado com o gasto atual.

## Regras

- Não alterar nada na conta durante a auditoria. Terminar listando o que será alterado quando o usuário aprovar.
- Ao aplicar depois, uma mudança por vez, relendo a conta para confirmar cada uma.
- Guardar uma leitura completa do estado anterior antes da primeira alteração. É o que permite voltar atrás.
- Sem emoji e sem travessão no relatório. Português do Brasil, direto.
- Toda afirmação com número do lado. Dizer também o que está certo, não só o que está errado.

## Pegadinhas da API (aparecem na hora de aplicar)

- **Campanha antiga e geografia.** Criar ou remover critério de localização em campanha antiga dá `MISSING_EU_POLITICAL_ADVERTISING_SELF_DECLARATION`. Antes, atualizar a campanha com `contains_eu_political_advertising = 3`.
- **Conversões hospedadas pelo Google.** Ações de rota, cliques pra ligar e "local actions" dão `MUTATE_NOT_ALLOWED` ao mudar `primary_for_goal`. Quem controla o lance é a meta: `customer_conversion_goal` e `campaign_conversion_goal`, campo `biddable`.
- **Booleano falso some do update.** `protobuf_helpers.field_mask` ignora campo booleano com valor `False` (default do proto3), então desligar rede de parceiros ou display exige montar o `update_mask.paths` explícito. O mutate reporta sucesso e nada muda. Sempre reler depois.
- **Unidade de orçamento.** A API usa micros. Conferir a unidade que o script em uso espera antes de mandar, e reler o orçamento depois de alterar.
- **Mutações são atômicas por lote.** Se uma operação do lote falha, nenhuma é aplicada. Isso é bom: evita meio caminho.
