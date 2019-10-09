FROM python:3.7

ENV JWT_ALGORITHM "HS512"
ENV JWT_ISSUER "oriole-issuer"
ENV JWT_AUDIENCE "oriole-service"
ENV JWT_SECRET "nosecret"
ENV JWT_TTL "3600"

RUN pip install -r requirements.txt
