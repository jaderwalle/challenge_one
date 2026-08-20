#!/usr/bin/env bash
#
# Provisiona a infraestrutura do agente na OCI: compartment, VCN, internet gateway,
# rota default, security list, subnet publica e a VM Compute (Always Free).
#
# Rodar no Cloud Shell da OCI, que ja vem com o `oci` autenticado na sua tenancy:
#   bash scripts/oci/provisionar.sh
#
# O script e IDEMPOTENTE: cada recurso e procurado pelo display-name antes de ser
# criado. Isso nao e capricho -- o shape A1.Flex do Always Free vive devolvendo
# "Out of host capacity", e a forma de conseguir a VM e re-rodar. Sem idempotencia,
# cada tentativa deixaria uma VCN orfa para tras.
#
# Nada de segredo aqui: os OCIDs sao descobertos em tempo de execucao e gravados
# FORA do repositorio, em ~/rag-fornecedor-oci.env.
set -euo pipefail

# ---------------------------------------------------------------- parametros
COMPARTMENT_NOME="rag-fornecedor"
VCN_NOME="vcn-rag-fornecedor"
VCN_CIDR="10.0.0.0/16"
SUBNET_NOME="subnet-publica"
SUBNET_CIDR="10.0.0.0/24"
IGW_NOME="igw-rag-fornecedor"
INSTANCIA_NOME="vm-rag-fornecedor"
PORTA_APP="${PORTA_APP:-8501}"          # Streamlit
UBUNTU_VERSAO="24.04"
# RSA 4096, e nao o ed25519 que seria o default moderno: o Cloud Shell roda em FIPS
# mode e o ssh-keygen recusa curvas Edwards com "ED25519 keys are not allowed in FIPS
# mode". RSA e o que a doc da OCI documenta para instancias, entao nao ha surpresa.
CHAVE_SSH="${CHAVE_SSH:-$HOME/.ssh/id_rsa}"
CHAVE_TIPO="${CHAVE_TIPO:-rsa}"
CHAVE_BITS="${CHAVE_BITS:-4096}"
SAIDA="$HOME/rag-fornecedor-oci.env"

# Shape preferido e fallback, exatamente como no PREMISSAS (P6/R2). 1 OCPU e 6 GB, e
# nao os 4/24 do teto Always Free, de proposito: pedido menor tem mais chance de achar
# capacidade, e a aplicacao nao carrega modelo local -- sao algumas centenas de vetores de 768 dims.
SHAPE_PREFERIDO="VM.Standard.A1.Flex"
SHAPE_CONFIG='{"ocpus":1,"memoryInGBs":6}'
SHAPE_FALLBACK="VM.Standard.E2.1.Micro"

# ---------------------------------------------------------------- utilidades
info() { echo ""; echo "==> $*"; }
ok()   { echo "    OK: $*"; }

# Normaliza a saida da CLI: uma consulta sem resultado devolve a string "null", que e
# nao-vazia -- sem isto, todo teste `[ -z ]` acharia que o recurso ja existe.
q() {
  local v
  v=$(eval "$1" 2>/dev/null || true)
  [ "$v" = "null" ] && v=""
  echo "$v"
}

command -v oci >/dev/null || { echo "ERRO: CLI 'oci' nao encontrado. Rode isto no Cloud Shell."; exit 1; }

# ---------------------------------------------------------------- tenancy
# No Cloud Shell a tenancy vem em OCI_TENANCY. Fora dele, cai para o ~/.oci/config.
TENANCY="${OCI_TENANCY:-}"
if [ -z "$TENANCY" ] && [ -f "$HOME/.oci/config" ]; then
  TENANCY=$(grep -m1 '^tenancy' "$HOME/.oci/config" | cut -d= -f2 | tr -d ' ')
fi
[ -n "$TENANCY" ] || { echo "ERRO: nao consegui descobrir o OCID da tenancy. Exporte OCI_TENANCY."; exit 1; }
info "Tenancy: $TENANCY"

# ---------------------------------------------------------------- chave SSH
# Gerada aqui no Cloud Shell (home persistente) porque o acesso a VM sera daqui. Para
# entrar de outra maquina depois, some a chave publica dela em ~/.ssh/authorized_keys
# na VM -- nunca copie esta privada para fora.
if [ ! -f "${CHAVE_SSH}.pub" ]; then
  info "Gerando par de chaves SSH ($CHAVE_TIPO $CHAVE_BITS) em $CHAVE_SSH"
  mkdir -p "$(dirname "$CHAVE_SSH")"
  chmod 700 "$(dirname "$CHAVE_SSH")"
  ssh-keygen -t "$CHAVE_TIPO" -b "$CHAVE_BITS" -N "" -C "rag-fornecedor" -f "$CHAVE_SSH"
fi
ok "chave publica: ${CHAVE_SSH}.pub"

# ---------------------------------------------------------------- compartment
info "Compartment '$COMPARTMENT_NOME'"
COMP=$(q "oci iam compartment list -c '$TENANCY' --all \
  --query \"data[?name=='$COMPARTMENT_NOME' && \\\"lifecycle-state\\\"=='ACTIVE'] | [0].id\" --raw-output")
if [ -z "$COMP" ]; then
  COMP=$(oci iam compartment create -c "$TENANCY" \
    --name "$COMPARTMENT_NOME" \
    --description "Agente RAG sobre os documentos do portal do fornecedor (challenge Alura/ONE)" \
    --wait-for-state ACTIVE --max-wait-seconds 300 \
    --query 'data.id' --raw-output)
  ok "criado"
else
  ok "ja existia"
fi
echo "    $COMP"

# ---------------------------------------------------------------- VCN
info "VCN '$VCN_NOME' ($VCN_CIDR)"
VCN=$(q "oci network vcn list -c '$COMP' --all \
  --query \"data[?\\\"display-name\\\"=='$VCN_NOME' && \\\"lifecycle-state\\\"=='AVAILABLE'] | [0].id\" --raw-output")
if [ -z "$VCN" ]; then
  VCN=$(oci network vcn create -c "$COMP" --cidr-blocks "[\"$VCN_CIDR\"]" \
    --display-name "$VCN_NOME" --dns-label "ragfornecedor" \
    --wait-for-state AVAILABLE --max-wait-seconds 300 \
    --query 'data.id' --raw-output)
  ok "criada"
else
  ok "ja existia"
fi

# A VCN nasce com uma route table e uma security list default. Reusar as duas mantem a
# topologia minima: criar novas deixaria as default orfas na VCN, o que so confunde
# quem for auditar o desenho depois.
RT=$(oci network vcn get --vcn-id "$VCN" --query 'data."default-route-table-id"' --raw-output)
SL=$(oci network vcn get --vcn-id "$VCN" --query 'data."default-security-list-id"' --raw-output)

# ---------------------------------------------------------------- internet gateway
info "Internet gateway '$IGW_NOME'"
IGW=$(q "oci network internet-gateway list -c '$COMP' --vcn-id '$VCN' --all \
  --query \"data[?\\\"display-name\\\"=='$IGW_NOME' && \\\"lifecycle-state\\\"=='AVAILABLE'] | [0].id\" --raw-output")
if [ -z "$IGW" ]; then
  IGW=$(oci network internet-gateway create -c "$COMP" --vcn-id "$VCN" --is-enabled true \
    --display-name "$IGW_NOME" --wait-for-state AVAILABLE --max-wait-seconds 300 \
    --query 'data.id' --raw-output)
  ok "criado"
else
  ok "ja existia"
fi

# ---------------------------------------------------------------- rota default
# Sem esta rota a VM ganha IP publico e mesmo assim nao fala com a internet -- e o
# sintoma e mudo: o `apt update` do cloud-init trava ate estourar timeout.
info "Rota 0.0.0.0/0 -> internet gateway"
oci network route-table update --rt-id "$RT" --force \
  --route-rules "[{\"destination\":\"0.0.0.0/0\",\"destinationType\":\"CIDR_BLOCK\",\"networkEntityId\":\"$IGW\"}]" \
  >/dev/null
ok "aplicada"

# ---------------------------------------------------------------- security list
# ATENCAO: `update` SUBSTITUI a lista inteira. Por isso a regra do SSH esta declarada
# aqui junto -- omiti-la nao "mantem o default", tranca voce para fora da VM.
info "Security list: libera 22 (SSH) e $PORTA_APP (aplicacao)"
oci network security-list update --security-list-id "$SL" --force \
  --ingress-security-rules "[{\"protocol\":\"6\",\"source\":\"0.0.0.0/0\",\"isStateless\":false,\"tcpOptions\":{\"destinationPortRange\":{\"min\":22,\"max\":22}},\"description\":\"SSH\"},{\"protocol\":\"6\",\"source\":\"0.0.0.0/0\",\"isStateless\":false,\"tcpOptions\":{\"destinationPortRange\":{\"min\":$PORTA_APP,\"max\":$PORTA_APP}},\"description\":\"Streamlit\"}]" \
  --egress-security-rules "[{\"protocol\":\"all\",\"destination\":\"0.0.0.0/0\",\"isStateless\":false,\"description\":\"saida liberada: a VM precisa alcancar a API do Gemini\"}]" \
  >/dev/null
ok "aplicada"

# ---------------------------------------------------------------- subnet publica
info "Subnet '$SUBNET_NOME' ($SUBNET_CIDR)"
SUBNET=$(q "oci network subnet list -c '$COMP' --vcn-id '$VCN' --all \
  --query \"data[?\\\"display-name\\\"=='$SUBNET_NOME' && \\\"lifecycle-state\\\"=='AVAILABLE'] | [0].id\" --raw-output")
if [ -z "$SUBNET" ]; then
  # prohibit-public-ip-on-vnic=false e o que torna a subnet "publica". Se sair true, a
  # VM sobe sem IP e o unico conserto e recriar a subnet.
  SUBNET=$(oci network subnet create -c "$COMP" --vcn-id "$VCN" --cidr-block "$SUBNET_CIDR" \
    --display-name "$SUBNET_NOME" --dns-label "publica" \
    --prohibit-public-ip-on-vnic false \
    --route-table-id "$RT" --security-list-ids "[\"$SL\"]" \
    --wait-for-state AVAILABLE --max-wait-seconds 300 \
    --query 'data.id' --raw-output)
  ok "criada"
else
  ok "ja existia"
fi

# ---------------------------------------------------------------- cloud-init
# Roda uma vez, no primeiro boot. Deixa a VM pronta para o deploy e ja resolve a
# pegadinha classica da imagem Ubuntu da OCI: alem da security list, existe um iptables
# no proprio SO que rejeita tudo que nao seja a porta 22. Sem isto, a porta aparece
# aberta no console e a aplicacao segue inalcancavel -- gasta-se uma tarde nisso.
USERDATA=$(mktemp)
{
  echo "#cloud-config"
  echo "package_update: true"
  echo "packages:"
  echo "  - python3-venv"
  echo "  - python3-pip"
  echo "  - git"
  echo "runcmd:"
  echo "  - [ bash, -lc, \"iptables -I INPUT 1 -p tcp --dport $PORTA_APP -m state --state NEW -j ACCEPT || true\" ]"
  echo "  - [ bash, -lc, \"netfilter-persistent save || true\" ]"
} > "$USERDATA"

# ---------------------------------------------------------------- imagem + VM
info "Instancia '$INSTANCIA_NOME'"
INST=$(q "oci compute instance list -c '$COMP' --all \
  --query \"data[?\\\"display-name\\\"=='$INSTANCIA_NOME' && \\\"lifecycle-state\\\"!='TERMINATED'] | [0].id\" --raw-output")

if [ -n "$INST" ]; then
  ok "ja existia"
else
  ADS=$(oci iam availability-domain list -c "$TENANCY" --query 'data[].name' --raw-output \
        | tr -d '[]", ' | grep -v '^$' | tr '\n' ' ')
  echo "    availability domains: $ADS"

  lancar() {  # $1 shape  $2 shape-config (vazio para shape de tamanho fixo)
    local shape="$1" cfg="$2" img ad
    local extra=()
    img=$(oci compute image list -c "$COMP" --operating-system "Canonical Ubuntu" \
      --operating-system-version "$UBUNTU_VERSAO" --shape "$shape" \
      --sort-by TIMECREATED --sort-order DESC --query 'data[0].id' --raw-output 2>/dev/null || true)
    if [ -z "$img" ] || [ "$img" = "null" ]; then
      echo "    sem imagem Ubuntu $UBUNTU_VERSAO para $shape"
      return 1
    fi
    [ -n "$cfg" ] && extra=(--shape-config "$cfg")
    for ad in $ADS; do
      echo "    tentando $shape em $ad ..."
      if oci compute instance launch -c "$COMP" --availability-domain "$ad" \
           --shape "$shape" ${extra[@]+"${extra[@]}"} --image-id "$img" --subnet-id "$SUBNET" \
           --assign-public-ip true --display-name "$INSTANCIA_NOME" \
           --ssh-authorized-keys-file "${CHAVE_SSH}.pub" --user-data-file "$USERDATA" \
           --wait-for-state RUNNING --max-wait-seconds 900 >/dev/null 2>/tmp/oci_launch_erro; then
        return 0
      fi
      # "Out of host capacity" e o erro ESPERADO do Always Free, nao falha do script:
      # so vale imprimir a mensagem crua quando for outra coisa.
      if grep -qi 'capacity' /tmp/oci_launch_erro; then
        echo "    sem capacidade neste AD"
      else
        echo "    ERRO:"
        sed 's/^/      /' /tmp/oci_launch_erro | head -20
      fi
    done
    return 1
  }

  if ! lancar "$SHAPE_PREFERIDO" "$SHAPE_CONFIG"; then
    echo ""
    echo "    $SHAPE_PREFERIDO indisponivel. Caindo para $SHAPE_FALLBACK (R2 do PREMISSAS)."
    if ! lancar "$SHAPE_FALLBACK" ""; then
      echo ""
      echo "ERRO: nenhum shape Always Free tinha capacidade agora."
      echo "Isto e esperado e nao exige mudar nada: re-rode este script mais tarde."
      echo "A rede ja esta provisionada -- a proxima execucao so tenta a VM."
      rm -f "$USERDATA"
      exit 1
    fi
  fi
  INST=$(q "oci compute instance list -c '$COMP' --all \
    --query \"data[?\\\"display-name\\\"=='$INSTANCIA_NOME' && \\\"lifecycle-state\\\"!='TERMINATED'] | [0].id\" --raw-output")
  ok "criada"
fi

IP=$(oci compute instance list-vnics --instance-id "$INST" --query 'data[0]."public-ip"' --raw-output)
rm -f "$USERDATA"

# ---------------------------------------------------------------- saida
# Gravado no HOME, nunca no repositorio: OCID nao e segredo, mas identifica a tenancy
# e este repo e publico.
{
  echo "# Gerado por scripts/oci/provisionar.sh -- nao versionar."
  echo "COMPARTMENT_ID=$COMP"
  echo "VCN_ID=$VCN"
  echo "SUBNET_ID=$SUBNET"
  echo "INSTANCIA_ID=$INST"
  echo "IP_PUBLICO=$IP"
  echo "PORTA_APP=$PORTA_APP"
  echo "CHAVE_SSH=$CHAVE_SSH"
} > "$SAIDA"

info "Pronto."
echo "    IP publico : $IP"
echo "    SSH        : ssh -i $CHAVE_SSH ubuntu@$IP"
echo "    App (depois do deploy) : http://$IP:$PORTA_APP"
echo "    OCIDs salvos em $SAIDA"
echo ""
echo "    O cloud-init leva ~2 min apos o boot para instalar python3-venv e abrir a"
echo "    porta $PORTA_APP no iptables do SO. Conferir na VM com:"
echo "      cloud-init status --wait && sudo iptables -L INPUT -n --line-numbers"
