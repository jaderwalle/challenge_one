# -*- coding: utf-8 -*-
"""Bateria de avaliacao contra o golden set. Gera relatorio versionado em avaliacao/.

    avaliar.py --retrieval                        # SO a busca -- nao gasta geracao
    avaliar.py --modelo <modelo-lite> --rpm 15    # bateria completa, cota alta
    avaliar.py --casos criticos --orcamento 20    # so os CRITICOS, no modelo de producao

A COTA DESENHA ESTE ARQUIVO. No free tier, cada modelo pleno da poucas dezenas de
requisicoes por DIA; os -lite dao centenas. Uma bateria completa nao cabe num dia no
modelo de producao. Por isso: --retrieval e gratuito, as respostas ficam em cache por
(caso, turno, modelo, hash da base), o grosso roda no -lite e so os CRITICOS rodam no
modelo de producao.

NUNCA rodar a bateria completa sem --modelo de cota alta.

ESQUELETO -- Marco E.
"""
import sys


def medir_retrieval(casos):
    """Para cada caso: o chunk esperado veio? Em que posicao? Com que score?

    E a metrica que mais importa e a mais barata -- resposta ruim com chunk errado
    nao se conserta no prompt. Rode isto sempre que mexer na base ou no chunking.
    """
    raise NotImplementedError  # TODO Marco E


def detectar_alucinacao(resposta, contexto):
    """Checagens automaticas, sem juiz humano. Cada uma e falha, nao ressalva:

      - cita secao que NAO estava no contexto recuperado;
      - cita documento inexistente;
      - afirma numero (prazo, percentual, valor) ausente do contexto;
      - responde sem citar fonte nenhuma;
      - recusa de escopo citando documento (recusa nao cita fonte).
    """
    raise NotImplementedError  # TODO Marco E


def main(argv):
    """Roda a bateria e grava o relatorio.

    O relatorio E EVIDENCIA VERSIONADA: nunca editar a mao. E precisa registrar, por
    caso, QUAL MODELO respondeu -- sem isso o numero final nao significa nada.
    """
    raise NotImplementedError  # TODO Marco E


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
