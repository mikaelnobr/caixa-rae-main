#!/bin/bash
# Configuration
domains=(extrator-rae.duckdns.org)
rsa_key_size=4096
data_path="./certbot"
staging=0 # Set to 1 if you're testing your setup to avoid hitting request limits

# Load .env
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Validate required env vars
if [ -z "$CERTBOT_EMAIL" ]; then
  echo "ERROR: CERTBOT_EMAIL is not set in .env"
  exit 1
fi

if [ -z "$DUCKDNS_TOKEN" ]; then
  echo "ERROR: DUCKDNS_TOKEN is not set in .env"
  exit 1
fi

# Enable exit on error
set -e

# Check DNS resolution before proceeding
echo "### Checking DNS resolution for ${domains[0]} ..."
MAX_RETRIES=10
RETRY_INTERVAL=15
for i in $(seq 1 $MAX_RETRIES); do
  RESOLVED_IP=$(getent hosts "${domains[0]}" | awk '{ print $1 }' || true)
  if [ -n "$RESOLVED_IP" ]; then
    echo "DNS resolved: ${domains[0]} -> $RESOLVED_IP"
    break
  fi
  echo "DNS not resolved yet. Attempt $i/$MAX_RETRIES. Retrying in ${RETRY_INTERVAL}s..."
  sleep $RETRY_INTERVAL
  if [ $i -eq $MAX_RETRIES ]; then
    echo "ERROR: Could not resolve ${domains[0]} after $MAX_RETRIES attempts."
    echo "Please check your DuckDNS configuration and try again."
    exit 1
  fi
done
echo

if [ -d "$data_path" ]; then
  read -p "Existing data found for $domains. Continue and replace existing certificate? (y/N) " decision
  if [ "$decision" != "Y" ] && [ "$decision" != "y" ]; then
    exit
  fi
fi

if [ ! -e "$data_path/conf/options-ssl-nginx.conf" ] || [ ! -e "$data_path/conf/ssl-dhparams.pem" ]; then
  echo "### Downloading recommended TLS parameters ..."
  mkdir -p "$data_path/conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$data_path/conf/options-ssl-nginx.conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$data_path/conf/ssl-dhparams.pem"
  echo
fi

echo "### Creating dummy certificate for ${domains[0]} ..."
path="/etc/letsencrypt/live/${domains[0]}"
mkdir -p "$data_path/conf/live/${domains[0]}"
docker compose run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1\
    -keyout '$path/privkey.pem' \
    -out '$path/fullchain.pem' \
    -subj '/CN=localhost'" certbot
echo

echo "### Starting nginx ..."
docker compose up --force-recreate -d nginx
echo

echo "### Deleting dummy certificate for ${domains[0]} ..."
docker compose run --rm --entrypoint "\
  rm -Rf /etc/letsencrypt/live/${domains[0]} && \
  rm -Rf /etc/letsencrypt/archive/${domains[0]} && \
  rm -Rf /etc/letsencrypt/renewal/${domains[0]}.conf" certbot
echo

echo "### Requesting Let's Encrypt certificate for ${domains[0]} ..."
# Join $domains to -d args
domain_args=""
for domain in "${domains[@]}"; do
  domain_args="$domain_args -d $domain"
done

# Enable staging mode if needed
if [ $staging != "0" ]; then staging_arg="--staging"; fi

docker compose run --rm \
  -e DUCKDNS_TOKEN=$DUCKDNS_TOKEN \
  --entrypoint "\
  certbot certonly \
    --authenticator dns-duckdns \
    --dns-duckdns-token \$DUCKDNS_TOKEN \
    --dns-duckdns-propagation-seconds 60 \
    $staging_arg \
    --email $CERTBOT_EMAIL \
    $domain_args \
    --rsa-key-size $rsa_key_size \
    --agree-tos \
    --force-renewal" certbot
echo

echo "### Reloading nginx ..."
docker compose exec nginx nginx -s reload
echo "### Certificate successfully retrieved and applied!"