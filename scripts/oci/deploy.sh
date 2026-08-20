#!/usr/bin/env bash
#
# Publica a aplicacao na VM da OCI: clona (ou atualiza) o repositorio, cria o venv,
# instala as dependencias, gera o indice vetorial e instala o servico systemd.
#
# Rodar DENTRO DA VM, como o usuario ubuntu (nao como root):
#   curl -fsSL https://raw.githubusercontent.com/DEFINIR-USUARIO/agente-rag-fornecedor/main/scripts/oci/deploy.sh | bash
# ou, se o repositorio ja estiver clonado:
#   bash scripts/oci/deploy.sh
#
# Idempotente: rodar de novo atualiza o codigo e reinicia o servico. Use --reindexar
# quando a base de conhecimento tiver mudado -- o indice e derivado dela.
set -euo pipefail

REPO="https://github.com/DEFINIR-USUARIO/agente-rag-fornecedor.git"
ALVO="${ALVO:-$HOME/rag-fornecedor}"
PORTA_APP="${PORTA_APP:-8501}"
SERVICO="rag-fornecedor"
REINDEXAR=0
[ "${1:-}" = "--reindexar" ] && REINDEXAR=1

info() { echo ""; echo "==> $*"; }
ok()   { echo "    OK: $*"; }
erro() { echo ""; echo "ERRO: $*"; exit 1; }

# ---------------------------------------------------------------- pre-requisitos
# Como root, o venv e o cache do pip nasceriam de root e o servico (que roda como
# ubuntu) nao conseguiria escrever nem ler direito. Falhar aqui e mais barato que
# depurar permissao depois.
[ "$(id -u)" -ne 0 ] || erro "nao rode como root. Use o usuario ubuntu; o script chama sudo onde precisa."

# O PORTAO DO SWAP. A VM caiu no fallback E2.1.Micro (1 GB) e a imagem Ubuntu da OCI
# sobe sem swap: o pip install do LangChain e morto pelo OOM killer no meio da
# resolucao de dependencias, e a unica pista que sobra e um "Killed" que nao diz que
# faltou memoria. Barato conferir, caro descobrir.
if [ -z "$(swapon --show --noheadings 2>/dev/null)" ]; then
  cat <<'AVISO'
ERRO: nenhum swap ativo.

Em 1 GB de RAM o `pip install` do LangChain e morto pelo OOM killer. Crie 2 GB antes:

  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile && sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
AVISO
  exit 1
fi
ok "swap ativo: $(swapon --show=SIZE --noheadings | tr -d ' ' | tr '\n' ' ')"

command -v git >/dev/null || erro "git ausente. Instale com: sudo apt install -y git"
python3 -m venv --help >/dev/null 2>&1 || erro "python3-venv ausente. Instale com: sudo apt install -y python3-venv"

# ---------------------------------------------------------------- codigo
info "Codigo em $ALVO"
if [ -d "$ALVO/.git" ]; then
  git -C "$ALVO" pull --ff-only
  ok "atualizado"
else
  git clone --depth 1 "$REPO" "$ALVO"
  ok "clonado"
fi
# Impresso de proposito: o indice e derivado da base, e base desatualizada gera um indice
# silenciosamente errado. Confira que o commit e o que voce espera.
echo "    commit: $(git -C "$ALVO" log -1 --oneline)"

cd "$ALVO"

# ---------------------------------------------------------------- venv + deps
info "Ambiente virtual e dependencias"
[ -d .venv ] || python3 -m venv .venv
PY=".venv/bin/python"

# COM cache e com paciencia, nao o contrario. A primeira versao disto usava
# --no-cache-dir para poupar os ~300 MB de cache, o que era zelo indevido: o boot volume
# Always Free tem 44 GB e estava em 6% de uso. O que de fato aconteceu no deploy real foi
# download interrompido no pyarrow (~49 MB) -- e sem cache, cada reexecucao rebaixa tudo
# de novo. Numa VM de 1 OCPU a rede e o gargalo, nao o disco.
"$PY" -m pip install --quiet --upgrade pip
"$PY" -m pip install --quiet --timeout 120 --retries 10 -r requirements.txt
# --format=freeze e nao `pip list`: o formato de tabela tem duas linhas de cabecalho, e
# somar cabecalho na contagem publica um numero errado num script que existe para dar
# confianca sobre o que subiu.
ok "$("$PY" -m pip list --format=freeze 2>/dev/null | wc -l) pacotes instalados"

# ---------------------------------------------------------------- .env
# A chave NAO entra neste script nem no repositorio. Se faltar, o deploy para aqui com
# instrucao: melhor parar antes de subir um servico que responderia erro a cada
# pergunta -- e que o avaliador veria como aplicacao quebrada.
info "Chave da API"
if [ ! -f .env ]; then
  cp .env.example .env
  erro "arquivo .env criado a partir do exemplo, mas SEM a chave.
Edite e preencha GOOGLE_API_KEY (gratuita, em https://aistudio.google.com/apikey):

  nano $ALVO/.env

Depois rode este script de novo."
fi
grep -qE '^GOOGLE_API_KEY=.+' .env || erro "GOOGLE_API_KEY vazia em $ALVO/.env. Preencha e rode de novo."
ok "presente"

# ---------------------------------------------------------------- indice
# Gerado com o servico AINDA PARADO, de proposito: em 1 GB, indexar com o Streamlit no
# ar coloca dois processos carregando o mesmo stack ao mesmo tempo.
info "Indice vetorial"
if [ ! -f indice/index.faiss ] || [ "$REINDEXAR" -eq 1 ]; then
  sudo systemctl stop "$SERVICO" 2>/dev/null || true
  "$PY" scripts/indexar.py --forcar
else
  ok "ja existe (use --reindexar para refazer apos mudar a base)"
fi

# ---------------------------------------------------------------- systemd
# Sem servico, a evidencia de deploy morre no primeiro reboot (PREMISSAS §5).
# --server.headless: sem isso o Streamlit tenta abrir navegador e pede e-mail no
# primeiro start, e o servico fica presoesperando um terminal que nao existe.
info "Servico systemd '$SERVICO'"
sudo tee "/etc/systemd/system/$SERVICO.service" >/dev/null <<UNIT
[Unit]
Description=RAG Portal do Fornecedor -- agente sobre manual, FAQ, politica e regulamento
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$(id -un)
WorkingDirectory=$ALVO
ExecStart=$ALVO/.venv/bin/streamlit run app/main.py \\
  --server.port=$PORTA_APP \\
  --server.address=0.0.0.0 \\
  --server.headless=true \\
  --browser.gatherUsageStats=false
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICO" >/dev/null
sudo systemctl restart "$SERVICO"
ok "habilitado no boot e iniciado"

# ---------------------------------------------------------------- verificacao
# Responder em localhost prova que o processo subiu; NAO prova que a porta esta
# alcancavel de fora (isso depende da security list e do iptables). Sao duas falhas
# diferentes e o texto abaixo as separa para nao mandar procurar no lugar errado.
info "Verificacao"
for _ in $(seq 1 20); do
  if curl -sf -o /dev/null "http://localhost:$PORTA_APP/_stcore/health"; then
    ok "aplicacao respondendo em localhost:$PORTA_APP"
    IP=$(curl -sf --max-time 5 https://ifconfig.me 2>/dev/null || echo "<IP da VM>")
    echo ""
    echo "    Acesse: http://$IP:$PORTA_APP"
    echo "    Logs:   sudo journalctl -u $SERVICO -f"
    exit 0
  fi
  sleep 3
done

echo ""
echo "ERRO: o servico nao respondeu em 60s. Veja o log:"
echo "  sudo journalctl -u $SERVICO -n 50 --no-pager"
exit 1
