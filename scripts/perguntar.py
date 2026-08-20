# -*- coding: utf-8 -*-
"""Interface de terminal do agente -- e a ferramenta de diagnostico do retrieval.

    perguntar.py "posso atrasar a entrega?"   # pergunta unica, SEM historico
    perguntar.py --scores "..."               # mostra os scores de cada chunk
    perguntar.py                              # modo conversa, COM historico

A distincao importa: o limiar de escopo e calibrado no regime de pergunta unica. Se
voce medir no modo conversa, a condensacao ja reescreveu a pergunta e o numero que
sair nao vale para o caso que o limiar precisa cobrir.

`--scores` e o que se usa no workflow /calibrar-limiar: mostra o score sem gastar
chamada de geracao.

ESQUELETO -- Marco C.
"""
import sys

from core import agente, config, documentos


def main(argv):
    raise NotImplementedError  # TODO Marco C


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
