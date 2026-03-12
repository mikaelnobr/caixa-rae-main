# Automações CAIXA RAE

Este repositório contém a aplicação Streamlit para o CAIXA RAE.

## Desenvolvimento Local (Sem Docker)

1. Crie um ambiente virtual e instale as dependências:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # No Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Configure os segredos:
   - Copie `.env.example` para `.env` e preencha o seu `GOOGLE_SHEET_ID`.
   - Coloque o seu `service_account.json` no diretório raiz.
3. Execute a aplicação:

   ```bash
   streamlit run app.py
   ```

## Desenvolvimento Local (Com Docker)

1. Certifique-se de que o Docker e o Docker Compose estão instalados.
2. Configure o seu `.env` e `service_account.json` no diretório raiz, conforme mencionado acima.
3. Execute a aplicação:

   ```bash
   docker compose up -d --build
   ```

4. Acesse a aplicação em `http://localhost`.

## Implantação com Docker em Oracle VM (Automatizada via GitHub Actions)

Esta aplicação é implantada usando o Docker Compose com um proxy reverso Nginx. As implantações são totalmente automatizadas via GitHub Actions ao enviar (push) para a branch `master`.

**CRÍTICO**: Certifique-se de nunca commitar o `.env` ou o `service_account.json` no repositório. Os arquivos `.gitignore` e `.dockerignore` estão configurados para evitar isso.

### Passo 1: Provisionar e Preparar a VM

1. **Provisionar VM**: Crie uma Instância de Computação na Oracle Cloud (Ubuntu ou Oracle Linux).
2. **Abrir Portas**:
   - No Console da Oracle Cloud, navegue até a sua instância -> Virtual Cloud Network -> Security List.
   - Adicione uma **Ingress Rule** (Regra de Entrada) permitindo tráfego TCP na porta `80` (HTTP) de origem `0.0.0.0/0`.
   - Certifique-se de que o firewall do sistema operacional também permite a porta 80. Por exemplo, no Ubuntu:

     ```bash
     sudo iptables -I INPUT -p tcp -m tcp --dport 80 -j ACCEPT
     sudo netfilter-persistent save
     ```

3. **Instalar Docker**:
   - Acesse a sua instância via SSH.
   - Instale o Docker Engine e o Docker Compose seguindo a [documentação oficial do Docker](https://docs.docker.com/engine/install/).
   - Certifique-se de que o seu usuário SSH (ex: `ubuntu` ou `opc`) seja adicionado ao grupo docker para que o uso do `sudo` não seja necessário:

     ```bash
     sudo usermod -aG docker $USER
     # Faça logoff e login novamente (ou reinicie) para que isso tenha efeito
     ```

### Passo 2: Fazer Upload dos Segredos para a VM

O fluxo de trabalho do GitHub Actions automatiza a transferência de código, mas ele **não** transfere os arquivos de segredos. Você deve fazer o upload destes manualmente uma vez para o diretório `~/caixa-rae` na VM.

```bash
# Na sua máquina local:
ssh user@<ip-da-sua-vm> "mkdir -p ~/caixa-rae"
scp .env user@<ip-da-sua-vm>:~/caixa-rae/.env
scp service_account.json user@<ip-da-sua-vm>:~/caixa-rae/service_account.json
```

### Passo 3: Configurar os GitHub Secrets

Para permitir que o GitHub Actions copie os arquivos com segurança e execute comandos na sua VM, acesse o seu **Repositório GitHub -> Settings -> Secrets and variables -> Actions**, e adicione os seguintes **Repository secrets** (Segredos do repositório):

- `ORACLE_VM_HOST`: O endereço IP público da sua VM Oracle.
- `ORACLE_VM_USERNAME`: O usuário SSH (ex: `ubuntu` ou `opc`).
- `ORACLE_VM_SSH_KEY`: A chave SSH **privada** (começa com `-----BEGIN...`) correspondente à chave pública instalada na VM.
- `ORACLE_VM_PORT`: (Opcional) A porta SSH. O padrão é `22` caso não seja definida.

### Passo 4: Implantação

Assim que os segredos estiverem configurados e os arquivos de segredos iniciais forem enviados para a VM:

1. Faça o commit e o push do seu código para a branch `master`.
2. Acesse a aba **Actions** no seu repositório GitHub para acompanhar a execução da implantação.
3. Assim que for concluído, acesse a aplicação em `http://<ip-da-sua-vm>/`.

O Nginx opera como um proxy reverso, encaminhando silenciosamente o tráfego da web e do WebSocket para a aplicação Streamlit em contêiner.

### Como Parar a Aplicação

```bash
docker compose down
```
