# -*- coding: utf-8 -*-
"""Aplicacao Streamlit: camada FINA sobre o core/.

Nenhuma regra de negocio aqui. Nenhum `st.` no core/. Enquanto isso valer, trocar o
Streamlit por uma API e criar uma pasta -- nao reescrever a aplicacao.

O historico da conversa vive no `st.session_state` e e passado para
`agente.responder(pergunta, historico=...)`. O core/ e stateless de proposito: nao ha
estado para sincronizar entre as duas camadas.

ESQUELETO -- Marco D.
"""
import streamlit as st

from core import agente, config


def tratar_erros_de_partida():
    """Os tres erros que o usuario final PODE encontrar, e que precisam de mensagem
    humana em vez de stack trace:

      1. GOOGLE_API_KEY ausente        -> "configure o .env" (nao "AuthenticationError")
      2. indice/ ausente ou defasado   -> "rode scripts/indexar.py"
      3. nenhum modelo respondeu       -> "cota do dia ou congestionamento; tente mais tarde"

    O terceiro e o que o avaliador tem chance real de ver. Stack trace na tela parece
    aplicacao quebrada mesmo quando o problema e cota de free tier.
    """
    raise NotImplementedError  # TODO Marco D


def main():
    """Chat + fontes + exemplos de pergunta.

    Exemplos na tela nao sao enfeite: sem eles o usuario nao sabe o que perguntar,
    faz uma pergunta fora de escopo, recebe recusa e conclui que a ferramenta nao
    funciona. Tres exemplos, um de documento diferente cada.

    As fontes vao expandidas por padrao: elas SAO o diferencial deste agente. Cada
    uma mostra documento, secao, pagina e versao.
    """
    raise NotImplementedError  # TODO Marco D


if __name__ == "__main__":
    main()
