# Agente RAG — Portal do Fornecedor

> **⚠️ Esqueleto.** Este README tem exatamente as seis seções cobradas pelo challenge, na
> ordem. Preencha conforme o projeto avança — **não deixe para o fim**: as seções de
> arquitetura e de exemplos são muito melhores quando escritas logo depois de cada marco,
> com a decisão fresca. Apague este aviso antes da entrega.

Agente de IA que responde perguntas sobre as regras de relacionamento entre a empresa e
seus fornecedores, com base em quatro documentos oficiais — manual, perguntas frequentes,
política e regulamento —, **sempre citando documento, seção e página**.

Projeto do Challenge Alura / ONE (Oracle Next Education).

> **Os documentos são fictícios**, criados para este projeto. Não representam nenhuma
> empresa real e não contêm dado pessoal.

---

## 1. Descrição geral

`<DEFINIR>` — o problema (o fornecedor recebe dezenas de páginas e tem uma pergunta
específica), o que o agente faz, e o que ele deliberadamente **não** faz: não decide sobre
fornecedor, não acessa sistema, não substitui o documento oficial.

## 2. Arquitetura da solução

```
[ navegador ] --:8501--> app/ (Streamlit) --> core/ buscar() + responder()
                                                 |              |
                                            FAISS local     Gemini API
```

Pipeline da base de conhecimento:

```
4 PDFs -> extrair.py -> texto limpo -> montar_base.py -> base_fornecedor.csv
       -> validar.py (portão) -> indexar.py -> índice FAISS
```

`<DEFINIR>` — explique as duas decisões que mais diferenciam este projeto:

- **1 seção = 1 chunk** (e, no FAQ, 1 pergunta = 1 chunk), em vez do splitter por
  caractere: partir um artigo do regulamento no meio entregaria meia regra ao usuário.
- **Precedência entre documentos**: quando eles divergem, o agente responde pelo mais
  normativo **e avisa que há divergência**, citando os dois.

## 3. Tecnologias e ferramentas

| Camada | Escolha |
|---|---|
| Linguagem | Python 3.12+ |
| Extração de PDF | `pypdf` |
| Orquestração | LangChain (uso enxuto: sem agent, tools ou memory) |
| Geração | Gemini Flash `<DEFINIR>`, com cascata de fallback |
| Embedding | `gemini-embedding-001`, 768 dimensões |
| Índice vetorial | FAISS local |
| Interface | Streamlit |
| Deploy | OCI Compute (Always Free), serviço `systemd` |

## 4. Como executar

```bash
git clone https://github.com/DEFINIR-USUARIO/agente-rag-fornecedor.git
cd agente-rag-fornecedor

python -m venv .venv
.venv/Scripts/activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env              # preencha GOOGLE_API_KEY (gratuita no AI Studio)

python dados/_trabalho/extrair.py
python dados/_trabalho/montar_base.py
python dados/_trabalho/validar.py       # portão: precisa sair com 0 erros
python scripts/indexar.py

python -m streamlit run app/main.py     # http://localhost:8501
```

A chave gratuita sai de <https://aistudio.google.com/apikey> e cobre geração e embedding.

## 5. Exemplos de perguntas

`<DEFINIR — pelo menos 6, cobrindo os quatro documentos e os três comportamentos>`

- Uma pergunta objetiva com resposta no regulamento
- A mesma pergunta em linguagem coloquial (mostra que o vocabulário de busca funciona)
- Uma pergunta cujos documentos divergem (mostra o aviso de divergência)
- Uma pergunta do domínio **sem** resposta nos documentos (mostra que o agente admite)
- Uma pergunta fora de escopo (mostra a recusa)
- Um follow-up curto ("e se atrasar?") depois de uma pergunta completa

## 6. Exemplos de respostas geradas

`<DEFINIR — cole respostas reais, com as fontes>` Inclua **pelo menos uma** resposta em
que o agente diz que não sabe. É o exemplo que mais convence: mostra que a citação de
fonte não é enfeite.

---

## Qualidade

`<DEFINIR>` — resumo dos portões: validador de base, testes sem rede, e a bateria do
golden set (com a ressalva de qual modelo respondeu cada caso). Relatórios em
[`avaliacao/`](avaliacao/).

## Deploy

Aplicação publicada em `<DEFINIR: http://IP:8501>` — ver
[`docs/deploy_oci.md`](docs/deploy_oci.md) para o procedimento completo e as evidências.

## Limitações conhecidas

- Sem HTTPS e sem domínio próprio: acesso por IP e porta. Não há dado sensível nem
  autenticação.
- Base fictícia, criada para o projeto — não vale como orientação real a fornecedor.
- Free tier do Gemini: em dia de uso intenso, a aplicação cai para um modelo `-lite`, que
  responde com menos qualidade.
- O agente não acessa sistema nenhum e não decide sobre nenhum fornecedor.

## Licença

`<DEFINIR>`
