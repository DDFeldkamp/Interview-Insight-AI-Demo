.PHONY: install install-dev install-api install-llm install-all test eval demo openai-demo serve clean

# Fast default install: enough for CLI demo + local synthesis.
install:
	python -m pip install --upgrade pip
	python -m pip install -e .

# Test/lint tools only. Keeps FastAPI/OpenAI out of the default environment.
install-dev:
	python -m pip install --upgrade pip
	python -m pip install -e ".[dev]"

# Web UI dependencies only.
install-api:
	python -m pip install --upgrade pip
	python -m pip install -e ".[api]"

# Optional OpenAI client only.
install-llm:
	python -m pip install --upgrade pip
	python -m pip install -e ".[llm]"

# Everything, for reviewers who want API + tests + OpenAI in one env.
install-all:
	python -m pip install --upgrade pip
	python -m pip install -e ".[all]"

test:
	PYTHONPATH=src pytest -q

eval:
	PYTHONPATH=src python -m gq_insight_copilot.cli evaluate --cases eval/eval_cases.json --out outputs/eval_results.json

demo:
	PYTHONPATH=src python -m gq_insight_copilot.cli synthesize --input sample_data/interviews --objective "Find onboarding and research-repository friction for product managers" --out outputs/demo_report.md --json

openai-demo:
	PYTHONPATH=src python -m gq_insight_copilot.cli synthesize --input sample_data/interviews --objective "What should we improve in the research workflow?" --provider openai --out outputs/openai_report.md --json

serve:
	uvicorn gq_insight_copilot.api:app --reload

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache outputs build dist *.egg-info src/*.egg-info
