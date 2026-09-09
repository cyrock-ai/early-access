# Development entry points. CI runs the same checks; see .github/workflows/python.yml.
PYTHON ?= python3
VENV   ?= .venv
BIN     = $(VENV)/bin

.PHONY: venv proto lint typecheck test integration check build clean

venv:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --quiet --upgrade pip
	$(BIN)/pip install --quiet -e . grpcio-tools==1.74.0 pytest ruff mypy

# Regenerates src/cyrock_db/_proto from ../proto/src/main/proto. Needs the reactor checkout.
proto:
	$(BIN)/python scripts/generate_proto.py

lint:
	$(BIN)/ruff check .
	$(BIN)/ruff format --check .

typecheck:
	$(BIN)/mypy

test:
	$(BIN)/pytest

# Starts a real CYROCK.AI DB via the reactor's Bootstrap runner. Needs a built reactor:
#   mvn -q -Ppinned-upstream install -DskipTests -Djacoco.skip=true
integration:
	CYROCK_IT=1 $(BIN)/pytest integration/ -v

check: lint typecheck test

build:
	$(BIN)/python -m build

clean:
	rm -rf dist build .pytest_cache .mypy_cache .ruff_cache src/cyrock_db/_proto/*_pb2*.py*
