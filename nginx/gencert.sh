#/bin/bash
openssl req -x509 -nodes -days 3065 \
  -newkey rsa:2048 \
  -keyout nginx/certs/selfsigned.key \
  -out nginx/certs/selfsigned.crt \
  -config nginx/openssl.cnf \
  -extensions req_ext