install-local:
	pip install -e ".[dev]"

test:
	pytest
