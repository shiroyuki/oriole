import os
import time
from typing import Any, Dict, Optional
from uuid import uuid4

from imagination import service
from imagination.decorator.config import Parameter
import jwt

from oriole.helper.logger_factory import LoggerFactory

logger = LoggerFactory.get(__name__)


@service.registered(params=[
    Parameter(name='algorithm', value=os.getenv('JWT_ALGORITHM') or 'HS512'),
    Parameter(name='issuer', value=os.getenv('JWT_ISSUER') or 'oriole-issuer'),
    Parameter(name='audience', value=os.getenv('JWT_AUDIENCE') or ''),
    Parameter(name='token_secret', value=os.getenv('JWT_SECRET') or ''),
    Parameter(name='default_ttl', value=int(os.getenv('JWT_TTL') or 3600)),
])
class Authenticator:
    def __init__(self, token_secret: str, issuer: str, audience: str, algorithm: str, default_ttl: int):
        self.algorithm = algorithm
        self.audience = audience
        self.issuer = issuer
        self.token_secret = token_secret
        self.default_ttl = default_ttl

    def encode_token(self, claims: Dict[str, Any], ttl: Optional[int] = None) -> str:
        self._check_readiness()

        return jwt.encode(self.auto_fill(claims, ttl),
                          self.token_secret,
                          algorithm=self.algorithm).decode()

    def decode_token(self, token: str) -> Dict[str, Any]:
        self._check_readiness()

        try:
            return jwt.decode(token,
                              self.token_secret,
                              issuer=self.issuer,
                              audience=self.audience,
                              algorithms=[self.algorithm])
        except jwt.exceptions.DecodeError:
            raise InvalidTokenError(token)
        except jwt.exceptions.ExpiredSignatureError:
            raise ExpiredTokenError(token)

    def auto_fill(self, claims: Dict[str, Any], ttl: Optional[int] = None) -> Dict[str, Any]:
        issue_time = int(time.time())
        expiration_time = issue_time + (ttl or self.default_ttl)

        default_claims = dict(
            iss=self.issuer,
            iat=issue_time,
            exp=expiration_time,
            aud=self.audience,
            jti=str(uuid4()),  # In this case, we only add "jti" as a decoy.
        )

        for k, v in default_claims.items():
            if k in claims and claims[k]:
                continue

            claims[k] = v

        return claims

    def _check_readiness(self):
        if not self.audience:
            raise MisconfigurationError('You must define an audience for the authenticator. Please define an environment variable "JWT_AUDIENCE".')

        if not self.token_secret:
            raise MisconfigurationError('You must define a token secret for the authenticator. Please define an environment variable "JWT_SECRET".')


class MisconfigurationError(AssertionError):
    pass


class InvalidCredentialError(AssertionError):
    pass


class InvalidTokenError(AssertionError):
    pass


class ExpiredTokenError(AssertionError):
    pass


class DisabledCredentialError(AssertionError):
    pass
