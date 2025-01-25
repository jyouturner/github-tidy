.PHONY: install test format lint clean deploy

install:
	poetry install

test:
	poetry run pytest

format:
	poetry run black .
	poetry run isort .

lint:
	poetry run black . --check
	poetry run isort . --check
	poetry run mypy src/

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +

deploy:
	./deploy.sh 