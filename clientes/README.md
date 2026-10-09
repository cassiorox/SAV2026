# Clientes

Cada cliente tem sua própria pasta aqui dentro, e cada pasta tem (no mínimo) um `contexto.md`.

```
clientes/
  _template/
    contexto.md      ← modelo, não é um cliente real
  nome-do-cliente/
    contexto.md      ← contexto daquele cliente
    estudos/
      persona.md     ← estudo de persona
      mercado.md     ← estudo de mercado
  outro-cliente/
    contexto.md
```

## Como adicionar um cliente

Rode **`/onboarding`**: você passa site, Instagram e Google Meu Negócio (ou só um briefing), o Claude puxa as informações, cria a pasta, o `contexto.md` e gera os estudos de persona e de mercado.

Os estudos também rodam sozinhos depois: `/estudo-persona` e `/estudo-mercado`.

## Por que isso importa

Quando você pedir pra criar algo pra um cliente (criativo, campanha, proposta, copy),
o Claude lê o `contexto.md` daquele cliente primeiro pra calibrar tudo ao negócio dele.

Recomendado que **todo cliente tenha um `contexto.md`**. Se faltar, o Claude vai sugerir rodar `/onboarding`.
