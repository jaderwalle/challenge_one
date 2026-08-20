# -*- coding: utf-8 -*-
"""Golden set: as perguntas com que o agente e medido.

QUATRO familias, e as quatro sao obrigatorias. Faltando qualquer uma, a bateria
mede otimismo em vez de qualidade.

ESQUELETO -- Marco E. Escreva os casos DEPOIS de os documentos existirem, mas ANTES
de ajustar prompt: caso escrito depois do ajuste tende a ser escrito para passar.
"""

# Casos marcados CRITICO rodam no modelo de producao (cota baixa). O resto roda no
# -lite. O relatorio registra qual modelo respondeu cada caso -- medir num e afirmar
# sobre outro e mentira, e e facil de cometer sem querer.

CASOS = [
    # ----------------------------------------------------------------- POSITIVOS
    # Pergunta legitima com resposta nos documentos.
    # {
    #     "id": "P01",
    #     "familia": "positivo",
    #     "critico": True,
    #     "pergunta": "Qual o prazo para o fornecedor emitir a nota fiscal?",
    #     "chunk_esperado": "regulamento-art-22",   # o que o retrieval deve trazer
    #     "deve_conter": ["5 dias uteis"],          # informacao que a resposta precisa ter
    #     "deve_citar": "regulamento",
    # },

    # ----------------------------------------------------------------- COLOQUIAIS
    # A mesma pergunta na linguagem de quem NAO leu o documento. Mede `termos_busca`.
    # "posso atrasar a entrega?" contra "Do inadimplemento contratual".

    # ------------------------------------------------------- NEGATIVOS DE ESCOPO
    # Pergunta alheia (receita de bolo, ferias, futebol). Espera-se recusa SEM citar
    # documento nenhum -- citar fonte numa recusa sugere que a base tem algo sobre o
    # assunto.

    # ---------------------------------------------------- NEGATIVOS DE COBERTURA
    # Pergunta DO dominio cuja resposta nao esta nos documentos. Espera-se "isso nao
    # consta nos documentos", nunca invencao. E a familia que mais separa um RAG
    # honesto de um chat bonitinho -- e a que quase todo projeto esquece.

    # ---------------------------------------------------------------- DIVERGENCIA
    # Pergunta cujos documentos se contradizem. Espera-se resposta pela precedencia
    # E o aviso de divergencia, citando os dois. Plante as divergencias de proposito
    # ao escrever os documentos e registre-as aqui.

    # ------------------------------------------------------------------ MULTITURNO
    # Par de turnos: pergunta completa seguida de follow-up curto ("e se atrasar?").
    # Mede a condensacao. Sem ela, o follow-up leva recusa de escopo -- um erro
    # visivel numa pergunta legitima.
]
