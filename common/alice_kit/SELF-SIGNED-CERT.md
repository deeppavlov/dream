## How To Create a Self-Signed Certificate

### Create `configuration.cnf` file
```
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = WA
L = Seattle
O = OrgName
CN = CompanyName

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @subject_alternate_names

[subject_alternate_names]
DNS.1 = something.my-domain-name.com
```

### Generate private key and certificate
```
openssl genrsa -out private-key.pem 2048
openssl req -new -x509 -days 365 \
            -key private-key.pem \
            -config configuration.cnf \
            -out certificate.pem
```

### Test it
First, deploy a basic https server, e.g. running an `openssl s_server` command (use `-accept` flag to specify the port, in this case it's `4243`)
```
openssl s_server -accept 4243 -cert certificate.pem -key private-key.pem -WWW
```

Run the following command substituting `https://something.my-domain-name.com:4243` with your deployment url.
This will output your self-signed certificate info.
```
curl --insecure -vvI https://something.my-domain-name.com:4243 2>&1 | awk 'BEGIN { cert=0 } /^\* SSL connection/ { cert=1 } /^\*/ { if (cert) print }'
```
