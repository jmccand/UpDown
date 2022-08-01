import jwt
import cryptography
import local

with open(local.PATH_TO_RSA_PUB, 'r') as public:
    with open(local.PATH_TO_RSA_PRIV, 'r') as private:
        private_key = private.read()
        public_key = public.read()
        encoded = jwt.encode({"some": "payload"}, private_key, algorithm="RS256")
        print(encoded)
        decoded = jwt.decode(encoded, public_key, algorithms=["RS256"])
        print(decoded)
