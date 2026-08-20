# `dados/fontes/` — os quatro documentos

Aqui vivem os documentos que o agente consulta. Eles são **fictícios**, criados para este
projeto, e representam uma empresa fictícia (`<DEFINIR: nome>`).

```
fontes/
├─ manual.md        · manual.pdf        # manual do fornecedor
├─ faq.md           · faq.pdf           # perguntas frequentes
├─ politica.md      · politica.pdf      # política de relacionamento / compras
└─ regulamento.md   · regulamento.pdf   # regulamento (artigos)
```

## Por que o `.md` e o `.pdf` convivem

O `.md` é a **fonte da verdade**; o `.pdf` é gerado a partir dele e é o que o pipeline lê.

Isso dá três coisas que nenhum projeto com PDF de terceiro tem:

1. **Gabarito para validar a extração.** O validador compara as seções extraídas do PDF
   com as do Markdown e falha na divergência. É a defesa mais forte que existe contra
   extração suja — e o risco R5 das premissas é justamente esse.
2. **Editar documento é editar texto**, não diagramar de novo.
3. **O `diff` do git mostra a mudança de conteúdo**, não um binário opaco.

O pipeline continua lendo o **PDF**, sempre. Ler o `.md` no lugar seria trapaça: o
entregável do challenge é "código para ler e processar o documento".

## Ao escrever os documentos

- **Cabeçalho com versão e data** em cada um. A coluna `versao` do chunk sai daí, e é o
  que permite dizer ao usuário de qual versão veio a resposta.
- **Estrutura explícita e consistente**: o regulamento em artigos (`Art. 1º`, `Art. 2º`),
  a política em seções numeradas (`4`, `4.1`, `4.2`), o manual em títulos hierárquicos, o
  FAQ em pares pergunta/resposta. A regra de chunking depende disso.
- **Coluna única no PDF.** Layout de duas colunas sai embaralhado na extração, e a
  correção certa é regerar o PDF — não empilhar heurística no extrator.
- **Plante divergências de propósito** entre documentos (um prazo que o manual arredonda e
  o regulamento detalha, por exemplo). São os casos de teste mais valiosos do projeto.
  Registre cada uma em `docs/divergencias.md`.
- **Nada de dado pessoal.** Nome, e-mail, telefone, CNPJ: todos fictícios. E nada que
  identifique uma empresa real.

## Gerando os PDFs

Qualquer ferramenta serve — é passo de autoria, não entra no pipeline automatizado:

```bash
# exemplo com pandoc
pandoc manual.md -o manual.pdf --pdf-engine=xelatex -V mainfont="Calibri"
```

Regerou o PDF? Rode `/atualizar-base` (ou o pipeline inteiro) e **leia o `diff` do CSV**.
