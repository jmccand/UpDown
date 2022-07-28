import jwt
import cryptography

with open('test-rsa.pub', 'r') as public:
    with open('test-rsa', 'r') as private:
        private_key = private.read()
        public_key = public.read()
        encoded = jwt.encode({"some": "payload"}, private_key, algorithm="RS256")
        print(encoded)
        decoded = jwt.decode(encoded, public_key, algorithms=["RS256"])
        print(decoded)
