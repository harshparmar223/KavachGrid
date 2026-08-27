#!/bin/bash
# ============================================
# KAVACHGRID 3.0 — TLS Certificate Generator
# Generates self-signed certificates for MQTT
# ============================================

set -e

CERT_DIR="mqtt/certs"
mkdir -p "$CERT_DIR"

echo "=== Generating CA certificate ==="
openssl req -new -x509 -days 365 -extensions v3_ca \
    -keyout "$CERT_DIR/ca.key" \
    -out "$CERT_DIR/ca.crt" \
    -subj "/CN=KavachGrid CA/O=KavachGrid/C=IN" \
    -passout pass:kavachgrid

echo "=== Generating server key ==="
openssl genrsa -out "$CERT_DIR/server.key" 2048

echo "=== Generating server CSR ==="
openssl req -new \
    -key "$CERT_DIR/server.key" \
    -out "$CERT_DIR/server.csr" \
    -subj "/CN=kavachgrid-mqtt/O=KavachGrid/C=IN"

echo "=== Signing server certificate ==="
openssl x509 -req -days 365 \
    -in "$CERT_DIR/server.csr" \
    -CA "$CERT_DIR/ca.crt" \
    -CAkey "$CERT_DIR/ca.key" \
    -CAcreateserial \
    -out "$CERT_DIR/server.crt" \
    -passin pass:kavachgrid

echo "=== Cleaning up ==="
rm -f "$CERT_DIR/server.csr" "$CERT_DIR/ca.srl"

echo "=== TLS certificates generated in $CERT_DIR ==="
echo "  ca.crt     - CA certificate (distribute to clients)"
echo "  server.crt - Server certificate"
echo "  server.key - Server private key"
