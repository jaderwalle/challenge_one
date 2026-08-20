# Deploy na Oracle Cloud Infrastructure

Como a aplicação sai do notebook e vai para um IP público, usando só o **Always Free** da
OCI. Sem Docker, sem balanceador, sem domínio: uma VM, um serviço `systemd`, uma porta.

> **Status:** ⏳ nada executado ainda neste projeto. Os dois scripts (`provisionar.sh` e
> `deploy.sh`) vêm prontos e já rodaram ponta a ponta num projeto irmão — o que está
> descrito aqui é procedimento verificado, não teoria. Falta executar e anexar as
> evidências.

## Desenho

```
        internet
            |
            v  :22 (SSH)  :8501 (aplicação)
   +----------------------------+
   |  VCN  10.0.0.0/16          |
   |  +----------------------+  |
   |  | subnet pública       |  |
   |  |   10.0.0.0/24        |  |
   |  |   [ VM Ubuntu ]      |  |----> API do Gemini (egress liberado)
   |  +----------------------+  |
   |  internet gateway <--------+
   +----------------------------+
        compartment: rag-fornecedor
```

Três camadas precisam concordar para a porta 8501 responder, e é exatamente aí que o
deploy costuma travar:

| Camada | Onde se configura | Se faltar |
|---|---|---|
| Roteamento | rota `0.0.0.0/0` → internet gateway | a VM tem IP público e não alcança nada |
| Security list | regra de ingress na VCN | conexão morre sem resposta (timeout) |
| Firewall do SO | `iptables` dentro do Ubuntu | console mostra tudo aberto e mesmo assim dá timeout |

A terceira é a que engana: a imagem Ubuntu da OCI já vem com um `iptables` que rejeita
tudo fora da porta 22. O script abre as três de uma vez.

---

## 1. Infraestrutura ⏳

Tudo em um script idempotente — [`scripts/oci/provisionar.sh`](../scripts/oci/provisionar.sh).
Rodar no **Cloud Shell**, que já vem com a CLI `oci` autenticada:

```bash
git clone https://github.com/DEFINIR-USUARIO/agente-rag-fornecedor.git
cd agente-rag-fornecedor
bash scripts/oci/provisionar.sh
```

O que ele cria:

| Recurso | Nome | Detalhe |
|---|---|---|
| Compartment | `rag-fornecedor` | isola o projeto do resto da tenancy |
| VCN | `vcn-rag-fornecedor` | `10.0.0.0/16`, DNS label `ragfornecedor` |
| Internet gateway | `igw-rag-fornecedor` | + rota `0.0.0.0/0` na route table default |
| Security list | (a default da VCN) | ingress TCP 22 e 8501; egress liberado |
| Subnet pública | `subnet-publica` | `10.0.0.0/24`, IP público permitido |
| Chave SSH | `~/.ssh/id_rsa` | RSA 4096 (o Cloud Shell roda em FIPS mode e recusa Ed25519); gerada se ainda não existir |
| VM Compute | `vm-rag-fornecedor` | Ubuntu 24.04, `VM.Standard.A1.Flex` 1 OCPU / 6 GB — com fallback, veja abaixo |

O `cloud-init` da VM já instala `python3-venv`, `pip` e `git`, e insere a regra do
`iptables` para a porta da aplicação.

**Rodar de novo é seguro.** Cada recurso é procurado pelo `display-name` antes de ser
criado, então uma segunda execução não duplica nada — só tenta o que ainda falta.

### Quando o A1.Flex não tiver capacidade

`Out of host capacity` é o comportamento normal do Always Free, não um erro de
configuração. O script trata assim:

1. tenta o `VM.Standard.A1.Flex` em **cada** availability domain da região;
2. não conseguindo, cai para o `VM.Standard.E2.1.Micro` (x86, 1 OCPU / 1 GB) — o
   fallback declarado no risco R2 do `PREMISSAS.md`;
3. falhando os dois, sai com a rede já provisionada e a instrução de re-rodar.

Como a rede persiste, a segunda tentativa é só a VM e leva segundos. É por isso que
vale provisionar cedo: capacidade aparece e some, e ninguém quer descobrir isso na
véspera da entrega.

> **Foi o que aconteceu no projeto de origem, e é o cenário provável aqui.** Em
> `sa-saopaulo-1` — que tem **um único** availability domain, então o passo 1 não tem
> para onde tentar de novo — o A1.Flex estava sem capacidade e o deploy real rodou no
> `E2.1.Micro`: x86, 1 OCPU, **1 GB de RAM**. Duas consequências: a wheel `aarch64` do
> FAISS deixa de ser o caminho (a `x86_64` vale, e é ainda mais garantida) e o swap
> abaixo passa a ser **obrigatório**.

### Swap — obrigatório no E2.1.Micro

A imagem Ubuntu da OCI sobe **sem swap nenhum**. Em 1 GB de RAM, o `pip install` do
LangChain é morto pelo OOM killer no meio da resolução de dependências — e a mensagem
que sobra (`Killed`) não diz que faltou memória, o que faz perder tempo procurando erro
onde não tem.

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab   # sobrevive ao reboot
free -h
```

### O que o script devolve

OCIDs e IP público vão para `~/rag-fornecedor-oci.env`, **no home do Cloud Shell, fora do
repositório**. OCID não é segredo, mas identifica a tenancy — e este repositório é
público.

### Conferência

```bash
# na sua máquina, com o IP que o script imprimiu
ssh -i ~/.ssh/id_rsa ubuntu@<IP>

# dentro da VM: cloud-init terminou? a porta está aberta no SO?
cloud-init status --wait
sudo iptables -L INPUT -n --line-numbers | head

# a regra precisa aparecer ANTES do REJECT final -- depois dele, ela nunca é alcançada
# e o sintoma é o pior possível: console mostrando a porta aberta e timeout no navegador

# e precisa estar salva em disco, não só em memória: o `|| true` do cloud-init existe
# para não derrubar o boot, o que significa que ele engoliria uma falha em silêncio
sudo grep 8501 /etc/iptables/rules.v4 || sudo netfilter-persistent save
```

---

## 2. Runtime e publicação ⏳

Um script, rodado **dentro da VM** como o usuário `ubuntu` —
[`scripts/oci/deploy.sh`](../scripts/oci/deploy.sh):

```bash
curl -fsSL https://raw.githubusercontent.com/DEFINIR-USUARIO/agente-rag-fornecedor/main/scripts/oci/deploy.sh | bash
```

Ele clona (ou atualiza) o repositório em `~/rag-fornecedor`, cria o venv, instala as
dependências pinadas, gera o índice vetorial e instala o serviço `systemd` habilitado no
boot. Rodar de novo atualiza o código e reinicia o serviço; `--reindexar` refaz o índice
quando a base de conhecimento mudou.

**Na primeira execução ele para de propósito**, depois de criar o `.env` a partir do
exemplo: a chave da API não está no repositório e não deve estar. Preencha e rode outra
vez.

```bash
nano ~/rag-fornecedor/.env    # GOOGLE_API_KEY=...
```

Quatro coisas que o script se recusa a fazer, cada uma por um modo de falha concreto:

| Recusa | Por quê |
|---|---|
| Rodar como `root` | o venv nasceria de root e o serviço, que roda como `ubuntu`, não leria |
| Instalar sem swap ativo | em 1 GB o `pip install` do LangChain morre no OOM killer, e a única pista é um `Killed` |
| Subir o serviço sem `GOOGLE_API_KEY` | a aplicação responderia erro a cada pergunta e pareceria quebrada |
| Indexar com o serviço no ar | dois processos carregando o mesmo stack não caberiam na memória |

O `systemd` sobe o Streamlit com `--server.address=0.0.0.0` (sem isso ele escuta só em
localhost e a porta aberta não serve para nada) e `--server.headless=true` (sem isso ele
tenta abrir navegador e pede e-mail no primeiro start, e o serviço fica preso esperando
um terminal que não existe).

### Conferência

```bash
systemctl status rag-fornecedor
sudo journalctl -u rag-fornecedor -n 30 --no-pager
curl -sf -o /dev/null -w '%{http_code}\n' http://localhost:8501/_stcore/health
```

Responder em `localhost` prova que o processo subiu — **não** que a porta é alcançável de
fora, o que depende da security list e do `iptables`. São falhas diferentes, e confundi-las
manda procurar no lugar errado.

## 3. Evidências ⏳

Link público funcionando, print da aplicação respondendo uma pergunta e print do console
da OCI. Vale também reiniciar a VM uma vez: é o que prova que o serviço sobe sozinho.

---

## Desfazer

Não há script de destruição: a ordem importa (instância → subnet → gateway → VCN →
compartment) e um `delete` errado numa tenancy compartilhada custa caro. Pelo console,
termine a instância primeiro e, no fim, delete o compartment `rag-fornecedor` — ele só
aceita ser removido quando está vazio.
