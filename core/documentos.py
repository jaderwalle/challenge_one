# -*- coding: utf-8 -*-
"""Contrato entre a base de chunks e o índice vetorial: 1 linha do CSV = 1 chunk.

Mora no core/ e não no pipeline porque quem decide o que vai para o vetor é a
aplicação que consulta, não o script que monta a base. O pipeline em
`dados/_trabalho/` importa daqui — e assim o que ele valida é, por construção, a
mesma coisa que a aplicação indexa. Enquanto forem duas cópias, divergir em
silêncio é só questão de tempo.

Só stdlib, de propósito: este módulo é importado por scripts que rodam sem as
dependências da aplicação instaladas.
"""

# Documentos da base, na ORDEM DE PRECEDÊNCIA (do mais normativo ao mais didático).
# É esta ordem que resolve contradição entre documentos — ver PREMISSAS P5.
# TODO: confirmar a ordem com o dono do projeto antes de usar em produção.
PRECEDENCIA = ["regulamento", "politica", "manual", "faq"]

# Colunas obrigatórias. Chunk sem qualquer uma delas é ERRO no validador, não aviso:
# sem procedência completa a resposta não pode citar fonte, e sem citar fonte o
# agente vira um chat opinativo sobre normas.
COLUNAS_OBRIGATORIAS = [
    "id",            # estável entre regerações: "<documento>-<secao>", nunca sequencial
    "documento",     # um de PRECEDENCIA
    "secao",         # identificador legível: "Art. 14", "4.2", "FAQ 07"
    "titulo",
    "pagina",
    "versao",
    "resumo",
    "termos_busca",
    "texto",
]

# Rótulo legível -> coluna. A ordem é a ordem em que o modelo lê o bloco:
# procedência primeiro (para citar certo), texto integral por último (é o que ele
# deve usar como base da resposta).
CAMPOS_PAYLOAD = [
    ("Documento", "documento"),
    ("Seção", "secao"),
    ("Título", "titulo"),
    ("Página", "pagina"),
    ("Versão", "versao"),
    ("Texto", "texto"),
]


def texto_para_embedding(linha):
    """O que vai para o vetor.

    Deliberadamente NÃO inclui o texto integral. Num documento normativo, os termos
    burocráticos ("parágrafo único", "para os fins do disposto neste") são frequentes
    e quase idênticos entre seções: se entrassem, dominariam a similaridade e
    afogariam o que a pergunta tem de específico.

    `termos_busca` existe para o problema inverso: o fornecedor pergunta "posso
    atrasar a entrega?" e o regulamento diz "Do inadimplemento contratual". Sem essa
    ponte de vocabulário, os dois vetores não se encontram.
    """
    return " | ".join([
        linha["titulo"],
        linha["resumo"],
        linha["termos_busca"],
    ])


def payload_do_chunk(linha):
    """O bloco de contexto que o modelo lê DEPOIS de o chunk já ter sido selecionado.

    `resumo` e `termos_busca` ficam de fora: são instrumentos de recall, não
    conteúdo. No prompt só gastariam contexto e dariam ao modelo uma paráfrase para
    copiar em vez do texto oficial.
    """
    partes = []
    for rotulo, coluna in CAMPOS_PAYLOAD:
        valor = str(linha.get(coluna) or "").strip()
        # Campo vazio é omitido em vez de virar "Página:" em branco. Rótulo sem valor
        # é um convite para o modelo preencher o buraco com invenção.
        if valor:
            partes.append("%s: %s" % (rotulo, valor))
    return "\n".join(partes)


def citacao(linha):
    """Como a fonte aparece para o usuário. Uma função só, para que app/, core/ e a
    avaliação nunca formatem citação de jeitos diferentes -- o que faria o detector
    de alucinação da avaliação medir uma coisa e o usuário ver outra."""
    return "%s, %s (p. %s, v. %s)" % (
        linha["documento"].capitalize(), linha["secao"], linha["pagina"], linha["versao"],
    )


def peso_precedencia(documento):
    """Menor = mais normativo. Usado para ordenar trechos divergentes no prompt.

    Documento fora da lista vai para o fim em vez de estourar: base malformada é
    problema do validador, não deve derrubar a aplicação em produção.
    """
    try:
        return PRECEDENCIA.index(documento)
    except ValueError:
        return len(PRECEDENCIA)
