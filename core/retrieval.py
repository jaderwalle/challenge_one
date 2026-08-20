# -*- coding: utf-8 -*-
"""Retrieval: o ÚNICO módulo que sabe que FAISS e Gemini existem.

Toda a aplicação fala com a busca por `buscar(pergunta, k)`. Enquanto essa for a
única porta, trocar o motor vetorial é trocar este arquivo -- não reescrever a
aplicação. É a regra que contém o risco de ter escolhido LangChain.

ESQUELETO: as funções abaixo têm o contrato e as armadilhas documentados; o corpo é
trabalho do Marco C.
"""
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from core import config


def _embeddings():
    """Cliente de embedding. Uma instância por processo; o SDK já é thread-safe.

    ATENÇÃO à dimensão: em 768 dims o gemini-embedding-001 devolve vetores SEM
    normalizar (norma ~0,589). Só a saída de 3072 dims vem normalizada. Sem
    normalizar, produto interno NÃO é cosseno, o score sai numa escala sem
    significado, e qualquer limiar calibrado em cima dele é numerologia.
    """
    raise NotImplementedError  # TODO Marco C


def construir_indice(linhas, destino):
    """Cria o índice a partir das linhas da base e grava em `destino`.

    Duas coisas NÃO são opcionais e o indexador deve falhar se faltarem:

      normalize_L2=True
      distance_strategy=DistanceStrategy.MAX_INNER_PRODUCT

    Com as duas, o score volta a ser cosseno em [-1, 1] e o limiar de escopo passa a
    significar alguma coisa.

    O texto vetorizado sai de `core.documentos.texto_para_embedding` -- nunca do
    texto integral do chunk. O metadado carrega a linha inteira, porque é dele que
    sai o payload do prompt e a citação de fonte.
    """
    raise NotImplementedError  # TODO Marco C


def sanidade_normalizacao(indice):
    """Confere que a norma média dos vetores indexados é 1,0 (tolerância 1e-3).

    Existe porque a falta de normalização NÃO gera erro: o retrieval continua
    devolvendo chunks, só que ordenados por um número sem significado, e o limiar
    passa a recusar pergunta legítima. É uma regressão invisível -- e é por isso que
    `scripts/indexar.py` deve ABORTAR quando esta checagem falha, em vez de avisar.
    """
    raise NotImplementedError  # TODO Marco C


def carregar_indice():
    """Carrega o índice do disco, com mensagem útil se ele não existir.

    "Índice ausente" e "índice desatualizado" são erros diferentes: o primeiro se
    resolve rodando indexar.py, o segundo exige saber que a base mudou. Compare o
    hash da base com o registrado no manifesto e diga qual dos dois é.
    """
    raise NotImplementedError  # TODO Marco C


def buscar(pergunta, k=None):
    """A única porta do retrieval.

    Devolve uma lista de (linha, score), do mais similar ao menos, com score em
    cosseno. NÃO aplica o limiar de escopo: quem decide o que fazer com score baixo é
    `core.agente` -- misturar recuperação com política de resposta é o que torna
    impossível medir as duas separadamente na avaliação.
    """
    raise NotImplementedError  # TODO Marco C
