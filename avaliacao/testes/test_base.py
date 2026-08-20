# -*- coding: utf-8 -*-
"""Testes de integridade da base. Rodam SEM REDE -- nenhum aqui chama a API.

    .venv/Scripts/python.exe -m pytest avaliacao/testes -q

Estes testes funcionam desde o dia em que a base existir. Sao a rede de seguranca
mais barata do projeto: pegam o defeito de extracao antes de ele virar resposta ruim
para o usuario.
"""
import csv
import os

import pytest

from core import config, documentos

MIN_CARACTERES = 80      # abaixo disto quase sempre e cabecalho ou numero de pagina
MAX_CARACTERES = 6000    # acima disto a secao devia ter sido sub-dividida


def carregar():
    if not os.path.exists(config.CSV_BASE):
        pytest.skip("base ainda nao gerada -- rode o pipeline em dados/_trabalho/")
    # utf-8-sig, sempre. CP1252 nao gera erro: so degrada o embedding em silencio.
    with open(config.CSV_BASE, encoding=config.ENCODING_CSV, newline="") as f:
        return list(csv.DictReader(f))


@pytest.fixture(scope="module")
def linhas():
    return carregar()


def test_base_nao_esta_vazia(linhas):
    assert len(linhas) > 0


def test_todas_as_colunas_obrigatorias_existem(linhas):
    faltando = set(documentos.COLUNAS_OBRIGATORIAS) - set(linhas[0].keys())
    assert not faltando, "colunas ausentes: %s" % sorted(faltando)


def test_nenhum_campo_obrigatorio_vazio(linhas):
    # Chunk sem procedencia nao pode citar fonte -- e sem citar fonte o agente vira
    # um chat opinativo sobre normas.
    problemas = [
        "%s.%s" % (linha.get("id", "?"), coluna)
        for linha in linhas
        for coluna in documentos.COLUNAS_OBRIGATORIAS
        if not str(linha.get(coluna) or "").strip()
    ]
    assert not problemas, "campos vazios: %s" % problemas[:10]


def test_ids_sao_unicos(linhas):
    ids = [linha["id"] for linha in linhas]
    duplicados = {i for i in ids if ids.count(i) > 1}
    assert not duplicados, "ids duplicados: %s" % sorted(duplicados)


def test_documentos_estao_na_precedencia(linhas):
    desconhecidos = {
        linha["documento"] for linha in linhas
        if linha["documento"] not in documentos.PRECEDENCIA
    }
    assert not desconhecidos, "documento fora da precedencia: %s" % sorted(desconhecidos)


def test_todos_os_quatro_documentos_estao_presentes(linhas):
    # Um documento sumir inteiro da base e o defeito mais silencioso que existe: nada
    # falha, o agente so passa a nao saber um quarto do assunto.
    presentes = {linha["documento"] for linha in linhas}
    assert presentes == set(documentos.PRECEDENCIA), "faltando: %s" % (
        set(documentos.PRECEDENCIA) - presentes)


def test_nenhum_chunk_e_curto_demais(linhas):
    curtos = [linha["id"] for linha in linhas if len(linha["texto"]) < MIN_CARACTERES]
    assert not curtos, "chunks curtos (cabecalho ou numero de pagina?): %s" % curtos[:10]


def test_nenhum_chunk_e_longo_demais(linhas):
    longos = [linha["id"] for linha in linhas if len(linha["texto"]) > MAX_CARACTERES]
    assert not longos, "chunks longos (faltou sub-dividir): %s" % longos[:10]


def test_texto_nao_parece_truncado(linhas):
    # Comecar em minuscula ou terminar sem pontuacao quase sempre e corte de
    # extracao. Entregar meia regra ao usuario e o pior defeito possivel aqui.
    suspeitos = [
        linha["id"] for linha in linhas
        if linha["texto"][:1].islower() or linha["texto"].rstrip()[-1:] not in ".;:!?)\"'"
    ]
    assert not suspeitos, "texto possivelmente truncado: %s" % suspeitos[:10]


def test_nao_ha_hifenizacao_de_quebra_de_linha(linhas):
    # "forne- cedor" sobrevivendo na base significa que juntar_linhas() nao rodou.
    suspeitos = [linha["id"] for linha in linhas if "- " in linha["texto"]]
    assert not suspeitos, "hifenizacao de quebra nao tratada: %s" % suspeitos[:10]


def test_texto_para_embedding_nao_inclui_o_texto_integral(linhas):
    # Regressao classica: alguem "melhora" o recall jogando o texto todo no vetor, e
    # os termos burocraticos passam a dominar a similaridade.
    linha = linhas[0]
    assert linha["texto"] not in documentos.texto_para_embedding(linha)


def test_payload_do_chunk_traz_a_procedencia(linhas):
    payload = documentos.payload_do_chunk(linhas[0])
    for rotulo in ("Documento", "Secao", "Pagina"):
        assert rotulo in payload or rotulo.replace("Secao", "Seção") in payload
