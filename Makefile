.PHONY: install-uv lint fix-lint type-check unit-tests integration-tests

install-uv:
	curl -LsSf https://astral.sh/uv/install.sh | sh

lint:
	uv run ruff check --select I
	uv run ruff format --diff
	uv run yamllint -s -c .github/.yamllint .github/

fix-lint:
	uv run ruff check --select I --fix
	uv run ruff format
	uv run yamllint -c .github/.yamllint .github/

type-check:
	uv run mypy src/ tests/

unit-tests:
	uv run test_unit

integration-tests:
	uv run test_integration
