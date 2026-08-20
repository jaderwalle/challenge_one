# Divergências conhecidas entre os documentos

Registro das contradições entre manual, FAQ, política e regulamento. Documento normativo
diverge — o que não pode acontecer é o agente escolher em silêncio.

**Precedência vigente:** `<DEFINIR — sugestão: regulamento > política > manual > FAQ>`

Cada divergência registrada aqui precisa ter:

1. um **caso no golden set** (`avaliacao/casos.py`, família `divergencia`);
2. a confirmação de que a resposta esperada segue a precedência **e** menciona o conflito.

| # | Assunto | O que cada documento diz | Precede | Caso no golden set |
|---|---|---|---|---|
| 1 | `<ex.: prazo de emissão da NF>` | Manual §3.2: "até 5 dias" · Regulamento Art. 22: "5 dias úteis, prorrogáveis uma vez" | regulamento | `D01` |

## Divergências plantadas de propósito

Ao escrever os documentos, plante de 3 a 5 contradições realistas. São os casos de teste
mais valiosos do projeto: nenhum RAG de tutorial trata disso, e é exatamente o que
acontece em documentação corporativa de verdade.

Bons candidatos: prazos (dias corridos vs. úteis), percentuais de multa, número de vias de
um documento, canal oficial de contato, e o que o FAQ simplifica demais.
