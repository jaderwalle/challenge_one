# -*- coding: utf-8 -*-
"""Configuração central: uma fonte só para caminhos, modelos e limiares.

Os defaults aqui são EXATAMENTE os comentados no `.env.example`. Se divergirem, o
arquivo versionado que o avaliador lê vira mentira — e ele só descobre quando o
agente não se comporta como está documentado.

Caminhos resolvidos por `__file__`, nunca por `getcwd()`: na VM da OCI a aplicação
sobe por systemd, com o cwd em `/`. Caminho relativo funciona na máquina de
desenvolvimento e quebra exatamente no deploy, que é onde depurar custa caro.
"""
import os

from dotenv import load_dotenv

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(RAIZ, ".env"))

DIR_FONTES = os.path.join(RAIZ, "dados", "fontes")
CSV_BASE = os.path.join(RAIZ, "dados", "base_fornecedor.csv")
DIR_INDICE = os.path.join(RAIZ, "indice")
MANIFESTO = os.path.join(DIR_INDICE, "manifesto.json")

# utf-8-sig em toda leitura de CSV. CP1252 corrompe o dado em silêncio: nada estoura,
# o embedding de "cotaÃ§Ã£o" só não cai no mesmo lugar que o de "cotação". E o -sig
# faz o Excel abrir com acento correto, que é como a base é revisada por humano.
ENCODING_CSV = "utf-8-sig"

# TODO: confirmar no AI Studio a versão Flash disponível no dia da configuração.
MODELO_GERACAO = os.getenv("GEMINI_MODELO_GERACAO", "gemini-1.5-flash")

# Cascata de fallback. Não é excesso de zelo: o Flash de produção devolve
# "503 high demand" em horário de pico, e a cota diária do free tier é de poucas
# dezenas de requisições por modelo pleno. O ÚLTIMO DA FILA DEVE SER UM -lite, de
# outra família: ele dá centenas de requisições por dia. Sem isso, a aplicação
# publicada funciona quando o avaliador testa cedo e responde "nenhum modelo
# respondeu" quando ele volta à tarde -- o pior modo de falha possível.
MODELOS_FALLBACK = [m.strip() for m in os.getenv(
    "GEMINI_MODELOS_FALLBACK", "").split(",") if m.strip()]

MODELO_EMBEDDING = os.getenv("GEMINI_MODELO_EMBEDDING", "gemini-embedding-001")
DIMENSOES = int(os.getenv("EMBEDDING_DIMENSOES", "768"))

# 5 é ponto de partida herdado de um projeto com chunks menores. Seções de documento
# rendem payload maior, então o número certo aqui é provavelmente menor. MEDIR.
TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))

# Teto, não meta. Cada turno antigo entra só como pergunta + resposta, nunca com o
# contexto recuperado naquele turno -- isso somaria milhares de tokens por rodada e
# queimaria cota à toa.
HISTORICO_MAX_TURNOS = int(os.getenv("HISTORICO_MAX_TURNOS", "3"))

# Limiar de escopo, em similaridade de cosseno. O score só tem significado porque os
# vetores são normalizados no índice (ver core/retrieval.py).
#
# ESTE VALOR PRECISA SER MEDIDO NESTE PROJETO -- workflow /calibrar-limiar. Copiar o
# número de outro projeto é chute com aparência de decisão. Depois de medir, registre
# em docs/calibracao_limiar.md e atualize o comentário no .env.example.
#
#   score <  LIMIAR_ESCOPO ... ruído óbvio: recusa de escopo, sem citar documento
#                              nenhum, sem gastar chamada de modelo
#   score >= LIMIAR_ESCOPO ... vai para o modelo, que decide entre responder e dizer
#                              que o assunto não está nos documentos
LIMIAR_ESCOPO = float(os.getenv("LIMIAR_ESCOPO", "0.0"))  # TODO: medir e fixar

PRECEDENCIA_DOCUMENTOS = [d.strip() for d in os.getenv(
    "PRECEDENCIA_DOCUMENTOS", "regulamento,politica,manual,faq").split(",") if d.strip()]


def chave_api():
    """Devolve a GOOGLE_API_KEY, falhando cedo e com instrução se faltar.

    Sem esta checagem, a ausência da chave só aparece lá adiante como erro de
    autenticação do SDK, longe da causa e sem dizer o que fazer.
    """
    chave = (os.getenv("GOOGLE_API_KEY") or "").strip()
    if not chave:
        raise RuntimeError(
            "GOOGLE_API_KEY ausente. Copie .env.example para .env e preencha a chave "
            "(gratuita, em https://aistudio.google.com/apikey)."
        )
    return chave

