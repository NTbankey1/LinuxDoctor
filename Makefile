.PHONY: setup lint format test clean train train-quick train-report train-dataset

setup:
	uv sync

lint:
	uv run ruff check src/ tests/ scripts/

format:
	uv run ruff format src/ tests/ scripts/
	uv run ruff check --fix src/ tests/ scripts/

test:
	uv run pytest -v --tb=short

clean:
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +

# ── Training ──────────────────────────────────────────────

train:  ## Train all ML models (default hyperparameters)
	uv run python scripts/train.py

train-quick:  ## Quick training (fewer iterations for testing)
	uv run python scripts/train.py --quick

train-report:  ## Train all models and export JSON evaluation report
	uv run python scripts/train.py --report

train-dataset:  ## Generate synthetic dataset, then train
	uv run python scripts/generate_dataset.py && uv run python scripts/train.py
