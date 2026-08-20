# -*- coding: utf-8 -*-
"""Etapa 3 do pipeline: o PORTAO. Sai com 1 se houver erro; 0 se so houver avisos.

    .venv/Scripts/python.exe dados/_trabalho/validar.py

A distincao entre erro e aviso nao e pedantismo -- e o que impede a base de apodrecer:

  ERRO  -> corromperia a base ou quebraria a citacao de fonte. Bloqueia o pipeline.
  AVISO -> pode estar certo, mas precisa de olho humano. Passa, e fica visivel.

REGRA DE OURO: nunca silenciar um aviso criando excecao para ele. Cada excecao e
individualmente razoavel; o conjunto e uma base em que ninguem mais confia. Confirme
a causa, corrija a origem, ou registre como divergencia conhecida.

ESQUELETO -- Marco B.
"""
import sys


# ------------------------------------------------------------------ ERROS (exit 1)

def erro_colunas_obrigatorias(linhas):
    """Todo chunk tem id, documento, secao, titulo, pagina, versao, resumo,
    termos_busca e texto? Sem procedencia completa a resposta nao pode citar fonte --
    e sem citar fonte o agente vira um chat opinativo sobre normas."""
    raise NotImplementedError  # TODO Marco B


def erro_id_duplicado(linhas):
    """id repetido significa que duas secoes colidiram na regra de nomeacao. O
    sintoma downstream e um chunk sumindo do indice sem aviso."""
    raise NotImplementedError  # TODO Marco B


def erro_encoding(caminho):
    """O arquivo abre como utf-8-sig? CP1252 nao gera erro: so faz o embedding de
    "cotaÃ§Ã£o" nao cair no mesmo lugar que o de "cotação"."""
    raise NotImplementedError  # TODO Marco B


def erro_documento_desconhecido(linhas):
    """Coluna `documento` fora da lista de precedencia. Chunk assim nunca seria
    ordenado corretamente numa divergencia."""
    raise NotImplementedError  # TODO Marco B


def erro_secao_ausente_no_extraido(linhas, gabarito_markdown):
    """SO se os PDFs forem gerados a partir de Markdown (ver insights §3).

    Compara a lista de secoes do .md original com a extraida do PDF. Divergencia
    significa extracao perdendo conteudo -- o defeito mais caro do projeto, e o unico
    que da para pegar automaticamente porque os documentos sao proprios.
    """
    raise NotImplementedError  # TODO Marco B


# ------------------------------------------------------------------ AVISOS (exit 0)

def aviso_chunk_curto_ou_longo(linhas):
    """Curto demais denuncia numero de pagina ou cabecalho virando secao. Longo
    demais denuncia secao que devia ter sido sub-dividida."""
    raise NotImplementedError  # TODO Marco B


def aviso_texto_truncado(linhas):
    """Chunk que comeca em minuscula ou termina sem pontuacao final. Quase sempre e
    corte de extracao -- e entregar meia regra ao usuario e o pior defeito possivel
    num agente sobre normas."""
    raise NotImplementedError  # TODO Marco B


def aviso_sem_termos_busca(linhas):
    """Secao sem vocabulario de recall so sera encontrada por quem ja usa o jargao do
    documento -- ou seja, por quem nao precisa do agente."""
    raise NotImplementedError  # TODO Marco B


def aviso_divergencia_entre_documentos(linhas):
    """Dois documentos falando do mesmo ponto com numeros diferentes (prazo,
    percentual, valor). Nao e erro: documento normativo diverge mesmo. Mas cada
    divergencia precisa estar na lista de divergencias conhecidas E no golden set."""
    raise NotImplementedError  # TODO Marco B


def main():
    """Roda tudo, imprime o relatorio e devolve o codigo de saida.

    Formato sugerido, porque relatorio ilegivel nao e lido:

        ERRO   [id-do-chunk] mensagem curta e o que fazer
        AVISO  [id-do-chunk] mensagem curta e o que conferir
        ---
        N linhas | X erros | Y avisos
    """
    raise NotImplementedError  # TODO Marco B


if __name__ == "__main__":
    sys.exit(main())
