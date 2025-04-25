export HTTPS_PROXY=http://localhost:8080
export HTTP_PROXY=http://localhost:8080
export SSL_CERT_FILE=/Users/takagi/.mitmproxy/mitmproxy-ca-cert.pem
export REQUESTS_CA_BUNDLE=/Users/takagi/.mitmproxy/mitmproxy-ca-cert.pem

litellm --config litellm.config --debug
