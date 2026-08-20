# -*- coding: utf-8 -*-
"""Gera o indice vetorial FAISS a partir da base de chunks.

    .venv/Scripts/python.exe scripts/indexar.py            # so se nao existir
    .venv/Scripts/python.exe scripts/indexar.py --forcar   # refaz do zero

O indice e ARTEFATO DERIVADO: fica fora do git, se regenera em segundos, e versionar
binario derivado so cria conflito e engorda o clone.

ESQUELETO -- Marco C.
"""
import sys

from core import config, documentos, retrieval


def manifesto(linhas):
    """Registra hash da base, modelo de embedding, dimensoes e contagem de chunks.

    Serve para distinguir "indice ausente" de "indice desatualizado" -- dois erros
    diferentes, com consertos diferentes. E acusa a troca do modelo de embedding, que
    invalida o indice inteiro em silencio: os vetores antigos continuam la, so nao
    significam mais a mesma coisa.
    """
    raise NotImplementedError  # TODO Marco C


def main():
    """Indexa e ABORTA se a sanidade de normalizacao falhar.

    Abortar, nao avisar: sem normalizacao o retrieval continua devolvendo chunks, so
    que ordenados por um numero sem significado -- e o limiar passa a recusar
    pergunta legitima. Regressao invisivel merece portao, nao aviso.

    Imprimir ao fim: numero de chunks, dimensoes, norma media e o tempo. A norma
    media impressa e o que faz alguem notar a regressao mesmo sem ler o codigo.
    """
    raise NotImplementedError  # TODO Marco C


if __name__ == "__main__":
    sys.exit(main())
