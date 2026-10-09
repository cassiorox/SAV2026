# Modelo: prompt do site (Lovable ou similar)

Trocar `{{GTM_ID}}` e `{{WHATSAPP_DDI_DDD_NUMERO}}`. Antes de usar, ler o prompt-base do site do cliente: se ele já define nomes de chave para o formulário, usar os mesmos e ajustar as variáveis `DLV - *` do GTM. Se o formulário não tem convênio, trocar `convenio` por um campo que exista (ex.: `servico`) aqui e no `gtm_build.py`.

Depois de preenchido, salvar em `clientes/<slug>/landing/prompt-lovable-rastreamento.md`.

---

```
Preciso instalar o rastreamento do site. Não altere design, textos nem rotas; mexa só no que está descrito abaixo.

1. GOOGLE TAG MANAGER
No index.html, colar o snippet abaixo o mais alto possível dentro do <head>:

<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','{{GTM_ID}}');</script>
<!-- End Google Tag Manager -->

E logo depois da abertura do <body>:

<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={{GTM_ID}}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->

Não instalar gtag.js, Google Analytics nem tag do Google Ads direto no código. Tudo passa pelo GTM.

2. EVENTO DE ENVIO DO FORMULÁRIO (lead_form)
Depois que o formulário for validado e o lead gravado no painel, antes de abrir o WhatsApp, fazer:

window.dataLayer = window.dataLayer || [];
let abriu = false;
const abrirWhatsApp = () => { if (abriu) return; abriu = true; window.location.href = urlWhatsApp; };
window.dataLayer.push({
  event: 'lead_form',
  pagina: '<slug da rota, ex.: {{slug}}>',
  convenio: '<valor do campo de atendimento, ex.: Convênio X ou Particular>',
  telefone: '<WhatsApp digitado no formato +55DDDNUMERO, só dígitos depois do +, ex.: +5511999998888>',
  eventCallback: abrirWhatsApp,
  eventTimeout: 800
});
setTimeout(abrirWhatsApp, 1500); // reserva se o GTM estiver bloqueado (adblock)

Regras:
- Disparar UMA vez por envio válido. Nunca no clique do botão se a validação falhar.
- O campo telefone precisa sair normalizado: remover espaços, parênteses e traços, e acrescentar +55 se a pessoa não digitou.
- Manter o estado "Abrindo o WhatsApp da recepção..." e o link "Não abriu? Toque aqui" já previstos.

3. LINKS DE WHATSAPP E DE ROTA
- Todo botão de WhatsApp que NÃO é o formulário (header, rodapé, botões soltos) deve ser um <a href="https://wa.me/{{WHATSAPP_DDI_DDD_NUMERO}}..."> de verdade, não um <button> com onClick. Não fazer dataLayer.push nesses cliques: o GTM já captura pelo link.
- O botão "Como chegar" deve ser um <a href> para o Google Maps do negócio (link maps.app.goo.gl ou google.com/maps).

4. PARÂMETROS DE CAMPANHA
Manter a captura já prevista: ler utm_source, utm_medium, utm_campaign, utm_term, utm_content, gclid e fbclid da URL na chegada, guardar em sessionStorage (com try/catch) e enviar nos campos ocultos do formulário.

Entrega: me diga em quais arquivos o snippet e o push foram colocados.
```

---

## O que o GTM já espera (não mudar os nomes)

| Chave no dataLayer | Usada em |
|---|---|
| `event: 'lead_form'` | Acionador `CE - lead_form` → GA4 `lead_form` + Ads "Lead formulario" |
| `pagina` | Parâmetro `pagina` no GA4 |
| `convenio` | Parâmetro `convenio` no GA4 |
| `telefone` (+55...) | Conversões otimizadas do Ads (vai em hash, não aparece no GA4) |
