
# Создаём приватный ключ
openssl genrsa -out nginx/certs/selfsigned.key 2048

# Создаём сертификат (CN обязательно должен быть localhost или ваш IP)
openssl req -new -x509 -key nginx/certs/selfsigned.key -out nginx/certs/selfsigned.crt -days 365 -subj "/CN=storefront.local"


