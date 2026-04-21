import requests
from jose import jwt, jwk
from jose.utils import base64url_decode
import json

def debug_jwks(token, jwks_url):
    print(f"Fetching JWKS from {jwks_url}...")
    try:
        jwks = requests.get(jwks_url).json()
        print("JWKS fetched successfully.")
        
        unverified_header = jwt.get_unverified_header(token)
        print(f"Token Header: {unverified_header}")
        kid = unverified_header.get('kid')
        
        # Find the correct key in JWKS
        key_data = None
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                key_data = key
                break
        
        if not key_data:
            print("No matching key found in JWKS for kid:", kid)
            return
        
        print("Found matching key in JWKS.")
        # Construct the public key
        # For RS256/ES256, jose can use the dict if we use jwk.construct
        public_key = jwk.construct(key_data)
        print("Public key constructed.")
        
        # Verify
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[unverified_header['alg']],
            options={"verify_aud": False}
        )
        print("Verification successful!")
        print("Payload:", payload)
        
    except Exception as e:
        print(f"Verification failed: {e}")

# I don't have a real token here, but I can check if the logic works except for the decode step
if __name__ == "__main__":
    # Just checking if jwk.construct works with a mock JWKS-like dict
    mock_key = {
        "kty": "RSA",
        "use": "sig",
        "kid": "test-kid",
        "alg": "RS256",
        "n": "...",
        "e": "AQAB"
    }
    try:
        k = jwk.construct(mock_key)
        print("Mock key construct works!")
    except Exception as e:
        print(f"Mock key construct failed: {e}")
