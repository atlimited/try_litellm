#!/bin/bash

# mitmproxy 証明書設定
export SSL_CERT_FILE=/Users/takagi/.mitmproxy/mitmproxy-ca-cert.pem
export REQUESTS_CA_BUNDLE=/Users/takagi/.mitmproxy/mitmproxy-ca-cert.pem

# プロキシ設定 - litellm プロキシ自体が mitmproxy を使用するように設定
export HTTP_PROXY=http://localhost:8080
export HTTPS_PROXY=http://localhost:8080
export http_proxy=http://localhost:8080
export https_proxy=http://localhost:8080

# デバッグモードで litellm プロキシを起動
litellm --config litellm.config --debug
