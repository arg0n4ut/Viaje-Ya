.PHONY: install install-dev build install-wheel clean test

install:
	@echo "Installing dependencies from requirements.txt..."
	pip install -r requirements.txt
	@echo "Installing build frontend..."
	pip install --upgrade build

install-dev:
	@echo "Installing dev tools..."
	pip install -r requirements.txt
	pip install --upgrade build

build:
	@echo "Building sdist and wheel..."
	python -m build

install-wheel: build
	@echo "Installing built wheel..."
	@python scripts/install_wheel.py

clean:
	@echo "Cleaning build artifacts..."
	@python -c "import shutil,glob; [shutil.rmtree(p, ignore_errors=True) for p in ('build','dist')]; [shutil.rmtree(egg, ignore_errors=True) for egg in glob.glob('*.egg-info')]; print('Removed build artifacts.')"

test:
	@echo "Running tests..."
	pytest