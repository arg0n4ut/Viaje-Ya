.PHONY: install test

install:
	@echo "Installing dependencies from requirements.txt..."
	pip install -r requirements.txt

test:
	@echo "Running tests..."
	pytest