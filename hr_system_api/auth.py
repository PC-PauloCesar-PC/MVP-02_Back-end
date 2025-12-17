import jwt
from jwt import PyJWKClient
from functools import wraps
from flask import request, jsonify, g
import os
from dotenv import load_dotenv
load_dotenv()

# --- CONFIGURAÇÕES ---

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
API_AUDIENCE = os.getenv("API_AUDIENCE")
ALGORITHMS = ["RS256"]

# Define o token de teste fixo para uso no Swagger
DEMO_TOKEN = os.getenv("DEMO_TOKEN")
# Payload básico que será injetado no Flask quando o token de teste for usado
TEST_USER_PAYLOAD = {"sub": "demo|test-user", "email": "swagger@test.com", "name": "Swagger Tester", "exp": 9999999999}


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

def get_token_auth_header():
    """Obtém o Access Token do cabeçalho Authorization."""
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError({"code": "authorization_header_missing", "description": "Authorization header is expected"}, 401)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError({"code": "invalid_header", "description": "Authorization header must start with Bearer"}, 401)
    elif len(parts) == 1:
        raise AuthError({"code": "invalid_header", "description": "Token not found"}, 401)
    elif len(parts) > 2:
        raise AuthError({"code": "invalid_header", "description": "Authorization header must be Bearer token"}, 401)

    token = parts[1]
    return token

def requires_auth(f):
    """Decorator para proteger rotas."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_auth_header()
        
        # VERIFICAÇÃO DE TESTE RÁPIDA: Se o token for o de demonstração, aceite-o
        if token == DEMO_TOKEN:
            g.current_user = TEST_USER_PAYLOAD
            return f(*args, **kwargs)
        
        # VERIFICAÇÃO REAL (Auth0)
        jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
        
        try:
            jwks_client = PyJWKClient(jwks_url, headers={'User-Agent': 'Mozilla/5.0'})
            
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer=f"https://{AUTH0_DOMAIN}/"
            )
            
            g.current_user = payload

        except jwt.ExpiredSignatureError:
            raise AuthError({"code": "token_expired", "description": "Token is expired"}, 401)
            
        except jwt.InvalidAudienceError:
            raise AuthError({"code": "invalid_audience", "description": "Incorrect audience, check your Auth0 configuration"}, 401)
            
        except jwt.InvalidIssuerError:
            raise AuthError({"code": "invalid_issuer", "description": "Incorrect issuer"}, 401)
            
        except jwt.PyJWKClientError as e:
            print(f"Erro no PyJWKClient: {e}")
            raise AuthError({"code": "keys_error", "description": "Unable to find appropriate key or connect to Auth0"}, 500)
            
        except jwt.PyJWTError as e:
            raise AuthError({"code": "invalid_header", "description": "Unable to parse authentication token."}, 400)
            
        return f(*args, **kwargs)
    return decorated