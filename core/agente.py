# -*- coding: utf-8 -*-
"""O agente: prompt, política de escopo, condensação de follow-up e `responder()`.

Este módulo NÃO imprime nada e NÃO sabe que o Streamlit existe. Quem chama decide
como mostrar o aviso de fallback de modelo -- `print` aqui é o mesmo pecado que um
`st.` seria.

ESQUELETO: o prompt abaixo já traz as regras que sustentam as premissas P5, P9 e
P10. O corpo das funções é trabalho dos Marcos C e D.
"""
from typing import NamedTuple

from core import config, documentos


class Resposta(NamedTuple):
    """Retorno de `responder()`. NamedTuple e não tupla crua: campo novo não quebra
    quem já desempacotava, e o call site fica legível (`r.fontes`, não `r[1]`)."""
    texto: str
    fontes: list          # lista de dicts com documento, secao, pagina, versao
    modelo: str           # qual modelo respondeu de fato -- a avaliação registra isto
    houve_fallback: bool
    fora_de_escopo: bool  # recusado pelo limiar, sem gastar chamada de modelo


PROMPT_SISTEMA = """Você é um assistente que responde perguntas sobre as regras de
relacionamento entre a empresa e seus fornecedores, com base EXCLUSIVAMENTE nos
trechos de documentos oficiais fornecidos no CONTEXTO.

Regras, em ordem de prioridade:

1. Responda SOMENTE com o que está no CONTEXTO. Se a informação não estiver lá, diga
   claramente que ela não consta nos documentos e sugira quem procurar. Nunca
   complete com conhecimento geral sobre contratos ou compras.
2. Cite a fonte de cada afirmação: documento, seção e página. Resposta sem fonte não
   serve -- o usuário precisa poder conferir.
3. Se os trechos do CONTEXTO se contradisserem sobre o mesmo ponto, responda pela
   ordem de precedência {precedencia} E AVISE que há divergência, citando os dois.
   Nunca escolha em silêncio.
4. Não decida nada sobre nenhum fornecedor concreto: você explica o que a regra diz.
   Não aprova cadastro, não julga proposta, não emite parecer.
5. Preserve prazos, percentuais e valores exatamente como estão no texto. Não
   arredonde, não converta, não "simplifique" número.
6. Responda em português do Brasil, direto, na linguagem de quem perguntou -- mas sem
   suavizar obrigação nem penalidade.
7. Turnos anteriores da conversa servem para entender a pergunta atual, NUNCA como
   fonte. Se a resposta depende de algo que você disse antes e que não está no
   CONTEXTO atual, diga isso em vez de repetir de memória.

CONTEXTO:
{contexto}
"""


def montar_contexto(resultados):
    """Monta o bloco CONTEXTO a partir dos chunks recuperados.

    Ordena por precedência do documento antes do score: quando dois trechos falam do
    mesmo ponto, o mais normativo aparece primeiro, e a regra 3 do prompt tem o que
    comparar. Usa `documentos.payload_do_chunk` -- nunca formate chunk aqui, senão a
    avaliação mede um formato e o usuário vê outro.
    """
    raise NotImplementedError  # TODO Marco C


def condensar(pergunta, historico):
    """Reescreve um follow-up como pergunta autônoma, ANTES de buscar.

    Existe porque multi-turno aqui é problema de RETRIEVAL, não de conversa: "e se eu
    atrasar?" vai crua ao índice, pontua abaixo do limiar e recebe recusa de escopo --
    um erro visível numa pergunta legítima.

    Só roda quando há histórico. Qualquer saída suspeita (vazia, longa demais, ou que
    perdeu o assunto) cai de volta na pergunta original: falha aqui não pode derrubar
    a resposta.
    """
    raise NotImplementedError  # TODO Marco D


def responder(pergunta, historico=None):
    """Pergunta -> Resposta. O `core/` é STATELESS: quem guarda a conversa é quem
    chama, e passa a lista de turnos aqui.

    Fluxo: condensar (se houver histórico) -> buscar -> aplicar LIMIAR_ESCOPO ->
    montar contexto -> chamar o modelo com cascata de fallback.

    Recusa por limiar acontece ANTES da chamada ao modelo -- é o que evita gastar
    cota com "qual a receita de brigadeiro". E recusa de escopo não cita documento
    nenhum: citar fonte numa recusa sugere que a base tem algo sobre o assunto.
    """
    raise NotImplementedError  # TODO Marco C
