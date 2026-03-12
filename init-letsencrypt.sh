#!/bin/bash

# =============================================================================
# Script de inicializacao do certificado HTTPS com DuckDNS + Let's Encrypt
# Variaveis lidas do arquivo .env
#
# Variaveis esperadas no .env:
#   DUCKDNS_TOKEN=seu-token
#   CERTBOT_EMAIL=seu@email.com
#   STAGING=0        (opcional, padrao 0; use 1 para testar sem consumir cota)
# =============================================================================

set -e

DOMAIN="extrator-rae.duckdns.org"
SUBDOMAIN="extrator-rae"

# --- CARREGAR .env ------------------------------------------------------------
if [ ! -f ".env" ]; then
  echo "Erro: arquivo .env nao encontrado. Execute na raiz do projeto."
  exit 1
fi

set -a
source .env
set +a

# --- VALIDACAO ----------------------------------------------------------------
if [[ -z "$DUCKDNS_TOKEN" ]]; then
  echo "Erro: variavel DUCKDNS_TOKEN nao definida no .env"
  exit 1
fi

if [[ -z "$CERTBOT_EMAIL" ]]; then
  echo "Erro: variavel CERTBOT_EMAIL nao definida no .env"
  exit 1
fi

STAGING="${STAGING:-0}"

# --- ATUALIZAR IP NO DUCKDNS --------------------------------------------------
echo "Atualizando IP no DuckDNS para o subdominio: $SUBDOMAIN"

RESPONSE=$(curl -s "https://www.duckdns.org/update?domains=${SUBDOMAIN}&token=${DUCKDNS_TOKEN}&ip=")
if [[ "$RESPONSE" != "OK" ]]; then
  echo "Falha ao atualizar DuckDNS. Resposta: $RESPONSE"
  exit 1
fi
echo "IP atualizado no DuckDNS."

# --- CRIAR DIRETORIOS ---------------------------------------------------------
mkdir -p ./certbot/conf/live/$DOMAIN ./certbot/www

# --- ARQUIVOS SSL NECESSARIOS ANTES DO NGINX SUBIR ----------------------------
# O nginx.conf usa options-ssl-nginx.conf e ssl-dhparams.pem.
# Esses arquivos precisam existir antes do container nginx iniciar.
OPTIONS_FILE="./certbot/conf/options-ssl-nginx.conf"
DHPARAMS_FILE="./certbot/conf/ssl-dhparams.pem"

if [ ! -f "$OPTIONS_FILE" ]; then
  echo "Baixando options-ssl-nginx.conf..."
  curl -fsSL https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf \
    -o "$OPTIONS_FILE"
fi

if [ ! -f "$DHPARAMS_FILE" ]; then
  echo "Gerando ssl-dhparams.pem (aguarde)..."
  openssl dhparam -out "$DHPARAMS_FILE" 2048 2>/dev/null
fi

# --- CERTIFICADO DUMMY --------------------------------------------------------
# O nginx.conf referencia fullchain.pem e privkey.pem.
# Precisam existir (mesmo que temporarios) para o nginx validar e subir.
CERT_DIR="./certbot/conf/live/$DOMAIN"

if [ ! -f "$CERT_DIR/fullchain.pem" ]; then
  echo "Gerando certificado temporario para o nginx conseguir subir..."
  docker run --rm \
    -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
    --entrypoint openssl \
    certbot/certbot \
    req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout "/etc/letsencrypt/live/$DOMAIN/privkey.pem" \
    -out "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" \
    -subj "/CN=$DOMAIN" 2>/dev/null
  echo "Certificado temporario criado."
fi

# --- SUBIR NGINX E STREAMLIT --------------------------------------------------
# --force-recreate garante que o nginx nao reutilize um container antigo
# que possa ter subido sem os arquivos ssl acima.
echo "Subindo containers nginx e streamlit_app..."
docker compose up -d --force-recreate nginx streamlit_app
sleep 5

# Validar que o nginx esta de pe
if ! docker compose exec nginx nginx -t 2>/dev/null; then
  echo "Erro: nginx falhou na validacao de configuracao."
  docker compose logs nginx
  exit 1
fi
echo "Nginx validado e rodando."

# --- SOLICITAR CERTIFICADO REAL -----------------------------------------------
STAGING_FLAG=""
if [ "$STAGING" -eq 1 ]; then
  STAGING_FLAG="--staging"
  echo "Aviso: modo staging ativado. O certificado nao sera confiavel, mas nao consome cota."
fi

echo "Solicitando certificado Let's Encrypt para $DOMAIN..."

# --entrypoint "" sobrescreve o entrypoint de renovacao automatica do container
# e executa o certonly diretamente
docker compose run --rm --entrypoint "" certbot \
  certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  $STAGING_FLAG \
  --email "$CERTBOT_EMAIL" \
  --agree-tos \
  --no-eff-email \
  -d "$DOMAIN"

if [ $? -ne 0 ]; then
  echo "Erro: falha ao obter certificado."
  echo "Verifique se a porta 80 esta acessivel externamente e se o DNS do DuckDNS propagou."
  exit 1
fi

# --- RECARREGAR NGINX COM CERTIFICADO REAL ------------------------------------
echo "Recarregando nginx com o certificado real..."
docker compose exec nginx nginx -s reload

echo "Configuracao concluida. Acesse: https://$DOMAIN"