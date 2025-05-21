INIT_FILE = src/what_cli/__init__.py

release:
	@VERSION=$$(grep -Po "__version__ = ['\"]([^'\"]+)['\"]" $(INIT_FILE) | cut -d'"' -f2); \
	echo "Current version: $$VERSION"; \
	if git rev-parse "v$$VERSION" >/dev/null 2>&1; then \
		echo "Error: Tag v$$VERSION already exists"; \
		exit 1; \
	fi; \
	git tag -a "v$$VERSION" -m "Release v$$VERSION"; \
	git push origin "v$$VERSION"; \
	echo "Pushed tag v$$VERSION"; \

install-local:
	pip install -e ".[dev]"

test:
	pytest
