PY3_VENV_PATH=.venv
TEST_CONFIG=JWT_ALGORITHM=HS512 \
		JWT_ISSUER=oriole-issuer \
		JWT_AUDIENCE=oriole-service \
		JWT_SECRET=nosecret \
		JWT_TTL=3600

venv:
	python3 -m venv $(PY3_VENV_PATH)

local-run:
	$(TEST_CONFIG) python3 -m oriole

local-jwt:
	$(TEST_CONFIG) g3 jwt:issue test test
